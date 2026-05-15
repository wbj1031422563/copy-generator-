"""FastAPI server — 学术辅导文案生成器 全功能工作台."""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import logging
import traceback

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

logger = logging.getLogger("copygen")

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.access_auth import (
    SESSION_KEY,
    auth_enabled,
    is_authenticated,
    is_public_path,
    session_secret,
    username,
    verify_credentials,
)
from core.generator import CopyGenerator
from core.ad_law_check import get_ad_law_checker
from core.anti_detect import AntiDetect
from core.data_loader import DATA_DIR, load_profile, load_services, load_style
from core.database import (
    add_good_copy,
    connect,
    db_info,
    delete_good_copy,
    init_schema,
    is_integrity_error,
    list_good_copies,
)
from llm.base import DummyLLM
from llm.openai_compat import OpenAICompat

app = FastAPI(title="学术辅导文案生成器", version="2.0.0")
STATIC = Path(__file__).parent / "static"
DIST = STATIC / "dist"
LLM_CONFIG_PATH = DATA_DIR / "llm_config.json"

anti_detect = AntiDetect()

init_schema()


class AccessAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not auth_enabled() or is_public_path(request.url.path):
            return await call_next(request)
        if is_authenticated(request.session):
            return await call_next(request)
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=401,
                content={"ok": False, "detail": "请先登录"},
            )
        return await call_next(request)


# Session outer (runs first), auth inner — order of add_middleware is reversed on request
app.add_middleware(AccessAuthMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret(),
    session_cookie="copygen_session",
    same_site="lax",
    https_only=False,
)


def _vue_built() -> bool:
    return (DIST / "index.html").is_file() and (DIST / "assets").is_dir()


def _spa_index_path() -> Path:
    if _vue_built():
        return DIST / "index.html"
    hint = STATIC / "build-required.html"
    if hint.is_file():
        return hint
    raise HTTPException(
        503,
        "前端未构建：请运行 cd web/frontend && npm install && npm run build",
    )


def _html_file(path: Path) -> FileResponse:
    """返回 HTML 静态文件（Windows 下使用绝对路径字符串，避免 500）。"""
    resolved = path.resolve()
    if not resolved.is_file():
        raise HTTPException(404, f"页面文件不存在: {resolved}")
    return FileResponse(str(resolved), media_type="text/html")


@app.exception_handler(Exception)
async def _unhandled_exception(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"ok": False, "detail": exc.detail},
        )
    logger.error("Unhandled %s %s: %s", request.method, request.url.path, exc)
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "detail": f"服务器内部错误: {exc}",
            "path": request.url.path,
        },
    )


if (DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=str(DIST / "assets")), name="dist_assets")


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "data": {
            "status": "up",
            "frontend": "vue" if _vue_built() else "missing_build",
            "database": db_info(),
            "auth_enabled": auth_enabled(),
        },
    }


@app.get("/api/auth/status")
async def auth_status(request: Request):
    enabled = auth_enabled()
    authed = is_authenticated(request.session)
    return {
        "ok": True,
        "data": {
            "enabled": enabled,
            "authenticated": authed if enabled else True,
            "username": request.session.get("user") if authed else None,
        },
    }


@app.post("/api/auth/login")
async def auth_login(request: Request):
    if not auth_enabled():
        return {"ok": True, "data": {"username": "local", "auth_disabled": True}}
    req = await _parse_json_body(request)
    user = str(req.get("username", ""))
    password = str(req.get("password", ""))
    if not verify_credentials(user, password):
        raise HTTPException(401, "用户名或密码错误")
    request.session[SESSION_KEY] = True
    request.session["user"] = username()
    return {"ok": True, "data": {"username": username()}}


@app.post("/api/auth/logout")
async def auth_logout(request: Request):
    request.session.clear()
    return {"ok": True, "data": {"logged_out": True}}


# ── Static / SPA ───────────────────────────────────────────
@app.get("/")
async def index():
    return _html_file(_spa_index_path())


# ── Generate ───────────────────────────────────────────────
@app.post("/api/generate")
async def generate(request: Request):
    req = await _parse_json_body(request)
    keywords = req.get("keywords", [])
    if not keywords:
        raise HTTPException(400, "keywords is required")

    use_llm = req.get("use_llm", False)
    style_override = req.get("style", None)
    version_count = req.get("version_count", 3)
    multi_style = req.get("multi_style", False)

    llm = None
    llm_provider = ""
    if use_llm:
        llm_cfg = {**_load_llm_config(), **req.get("llm", {})}
        if llm_cfg.get("api_key") == "__KEEP__":
            saved = _load_llm_config(raw=True)
            llm_cfg["api_key"] = saved.get("api_key", "")
        llm_provider = llm_cfg.get("provider", "")
        llm = _build_llm(llm_cfg)
        if not llm:
            raise HTTPException(
                400,
                "LLM 未配置：请在「设置 → LLM 配置」填写 API Key，"
                "或设置环境变量 DEEPSEEK_API_KEY / DASHSCOPE_API_KEY / OPENAI_API_KEY",
            )

    gen = CopyGenerator(llm_client=llm)
    _apply_generate_style(gen, style_override, version_count, multi_style)

    result = gen.generate(keywords, use_llm=bool(llm))
    result["generated_at"] = datetime.now(timezone.utc).isoformat()

    meta = {
        "violations_check": result.get("violations_check", {}),
        "version_count": version_count if style_override else version_count,
        "use_llm": use_llm,
        "llm_used": result.get("llm_used", False),
        "llm_provider": llm_provider if use_llm else "",
    }
    history_id = _save_history(
        keywords,
        style_override if style_override else "all",
        result["variants"],
        meta,
    )
    result["history_id"] = history_id

    return {"ok": True, "data": result}


# ── Batch generate ─────────────────────────────────────────
@app.post("/api/generate-batch")
async def generate_batch(request: Request):
    req = await _parse_json_body(request)
    keyword_sets = req.get("keyword_sets", [])
    style = req.get("style", "comprehensive")
    use_llm = req.get("use_llm", False)

    if not keyword_sets:
        raise HTTPException(400, "keyword_sets is required")

    llm = None
    llm_provider = ""
    if use_llm:
        llm_cfg = {**_load_llm_config(), **req.get("llm", {})}
        if llm_cfg.get("api_key") == "__KEEP__":
            llm_cfg["api_key"] = _load_llm_config(raw=True).get("api_key", "")
        llm_provider = llm_cfg.get("provider", "")
        llm = _build_llm(llm_cfg)
        if not llm:
            raise HTTPException(400, "LLM 未配置 API Key")

    results = []
    gen = CopyGenerator(llm_client=llm)
    for kw_set in keyword_sets:
        gen.style["version_count"] = 1
        gen.style["variants"] = {"v1": {"description": "标准版", "style": style}}
        result = gen.generate(kw_set, use_llm=bool(llm))
        meta = {
            "violations_check": result.get("violations_check", {}),
            "version_count": 1,
            "use_llm": use_llm,
            "llm_provider": llm_provider,
        }
        _save_history(kw_set, style, result["variants"], meta)
        results.append({
            "keywords": kw_set,
            "variants": result["variants"],
            "violations_check": result["violations_check"],
        })

    return {"ok": True, "data": {"results": results, "total": len(results)}}


# ── Database & quality examples ────────────────────────────
@app.get("/api/db-status")
async def get_db_status():
    return {"ok": True, "data": db_info()}


@app.get("/api/good-copies")
async def get_good_copies(limit: int = 20):
    return {"ok": True, "data": list_good_copies(limit=limit)}


@app.post("/api/good-copies")
async def create_good_copy(request: Request):
    req = await _parse_json_body(request)
    keywords = req.get("keywords", [])
    title = (req.get("title") or "").strip()
    body = (req.get("body") or "").strip()
    if not title or not body:
        raise HTTPException(400, "title and body are required")
    copy_id = add_good_copy(
        keywords=keywords,
        title=title,
        body=body,
        style=req.get("style", ""),
        note=(req.get("note") or "").strip(),
    )
    return {"ok": True, "data": {"id": copy_id}}


@app.delete("/api/good-copies/{copy_id}")
async def remove_good_copy(copy_id: int):
    if not delete_good_copy(copy_id):
        raise HTTPException(404, "not found")
    return {"ok": True}


# ── History ────────────────────────────────────────────────
@app.get("/api/history")
async def get_history(search: str = "", limit: int = 50):
    with connect() as db:
        if search:
            rows = db.execute(
                "SELECT * FROM history WHERE keywords LIKE ? ORDER BY id DESC LIMIT ?",
                (f"%{search}%", limit),
            ).fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    return {"ok": True, "data": [_history_row_to_dict(r) for r in rows]}


@app.get("/api/history/{id}")
async def get_history_item(id: int):
    with connect() as db:
        row = db.execute("SELECT * FROM history WHERE id = ?", (id,)).fetchone()
    if not row:
        raise HTTPException(404, "history not found")
    return {"ok": True, "data": _history_row_to_dict(row)}


@app.put("/api/history/{id}")
async def update_history_item(id: int, request: Request):
    req = await _parse_json_body(request)
    variants = req.get("variants")
    if variants is None:
        raise HTTPException(400, "variants is required")
    with connect() as db:
        row = db.execute("SELECT * FROM history WHERE id = ?", (id,)).fetchone()
        if not row:
            raise HTTPException(404, "history not found")
        meta = json.loads(row["meta"]) if row["meta"] else {}
        if "violations_check" in req:
            meta["violations_check"] = req["violations_check"]
        db.execute(
            "UPDATE history SET variants = ?, meta = ? WHERE id = ?",
            (
                json.dumps(variants, ensure_ascii=False),
                json.dumps(meta, ensure_ascii=False),
                id,
            ),
        )
    return {"ok": True}


@app.delete("/api/history")
async def clear_history():
    with connect() as db:
        db.execute("DELETE FROM history")
    return {"ok": True}


@app.delete("/api/history/{id}")
async def delete_history(id: int):
    with connect() as db:
        db.execute("DELETE FROM history WHERE id = ?", (id,))
    return {"ok": True}


# ── Templates ──────────────────────────────────────────────
@app.get("/api/templates")
async def get_templates():
    with connect() as db:
        rows = db.execute("SELECT * FROM templates ORDER BY updated_at DESC").fetchall()
    return {"ok": True, "data": rows}


@app.post("/api/templates")
async def create_template(request: Request):
    req = await _parse_json_body(request)
    name = req.get("name", "").strip()
    content = req.get("content", "")
    if not name:
        raise HTTPException(400, "name is required")
    now = datetime.now(timezone.utc).isoformat()
    try:
        with connect() as db:
            db.execute(
                "INSERT INTO templates (name, content, updated_at) VALUES (?, ?, ?)",
                (name, content, now),
            )
    except Exception as e:
        if is_integrity_error(e):
            raise HTTPException(409, f"模板 '{name}' 已存在") from e
        raise
    return {"ok": True, "data": {"name": name, "content": content, "updated_at": now}}


@app.put("/api/templates/{name}")
async def update_template(name: str, request: Request):
    req = await _parse_json_body(request)
    content = req.get("content", "")
    now = datetime.now(timezone.utc).isoformat()
    with connect() as db:
        db.execute(
            "UPDATE templates SET content = ?, updated_at = ? WHERE name = ?",
            (content, now, name),
        )
    return {"ok": True}


@app.delete("/api/templates/{name}")
async def delete_template(name: str):
    with connect() as db:
        db.execute("DELETE FROM templates WHERE name = ?", (name,))
    return {"ok": True}


# ── Dashboard & keywords ───────────────────────────────────
@app.get("/api/dashboard")
async def get_dashboard():
    from collections import Counter

    with connect() as db:
        total = db.execute("SELECT COUNT(*) as c FROM history").fetchone()["c"]
        template_count = db.execute("SELECT COUNT(*) as c FROM templates").fetchone()["c"]
        good_count = db.execute("SELECT COUNT(*) as c FROM good_copies").fetchone()["c"]
        rows = db.execute(
            "SELECT id, keywords, style, variants, meta, created_at FROM history ORDER BY id DESC LIMIT 8"
        ).fetchall()
        all_kw_rows = db.execute(
            "SELECT keywords FROM history ORDER BY id DESC LIMIT 200"
        ).fetchall()

    counter: Counter = Counter()
    for r in all_kw_rows:
        for kw in json.loads(r["keywords"]):
            counter[kw] += 1

    llm_raw = _load_llm_config(raw=True)
    provider = llm_raw.get("provider", "deepseek")
    llm_ok = bool(llm_raw.get("api_key") or _env_key(provider))

    return {
        "ok": True,
        "data": {
            "total_generations": total,
            "template_count": template_count,
            "recent": [_history_row_to_dict(r) for r in rows],
            "top_keywords": [{"word": w, "count": c} for w, c in counter.most_common(12)],
            "llm_configured": llm_ok,
            "llm_provider": provider,
            "good_copy_count": good_count,
            "database": db_info(),
        },
    }


@app.get("/api/keywords")
async def get_keyword_library():
    services = load_services()
    domains = services.get("domains", [])
    flat = []
    for d in domains:
        for kw in d.get("keywords", []):
            flat.append({"word": kw, "domain": d.get("name", "")})
    return {
        "ok": True,
        "data": {
            "domains": domains,
            "flat": flat,
            "service_types": services.get("service_types", []),
            "levels": services.get("levels", []),
        },
    }


# ── Stats ──────────────────────────────────────────────────
@app.get("/api/stats")
async def get_stats():
    with connect() as db:
        total = db.execute("SELECT COUNT(*) as c FROM history").fetchone()["c"]
        recent = db.execute(
            "SELECT keywords, created_at FROM history ORDER BY id DESC LIMIT 5"
        ).fetchall()
        template_count = db.execute("SELECT COUNT(*) as c FROM templates").fetchone()["c"]
        good_count = db.execute("SELECT COUNT(*) as c FROM good_copies").fetchone()["c"]

    return {"ok": True, "data": {
        "total_generations": total,
        "template_count": template_count,
        "good_copy_count": good_count,
        "recent": [{"keywords": json.loads(r["keywords"]), "created_at": r["created_at"]}
                    for r in recent],
    }}


# ── Profile / Services / Style / Sensitive words ───────────
@app.get("/api/profile")
async def get_profile():
    return {"ok": True, "data": load_profile()}


@app.put("/api/profile")
async def update_profile(request: Request):
    req = await _parse_json_body(request)
    (DATA_DIR / "profile.json").write_text(
        json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True}


@app.get("/api/services")
async def get_services():
    return {"ok": True, "data": load_services()}


@app.put("/api/services")
async def update_services(request: Request):
    req = await _parse_json_body(request)
    (DATA_DIR / "services.json").write_text(
        json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True}


# ── LLM config ─────────────────────────────────────────────
@app.get("/api/llm-config")
async def get_llm_config():
    raw = _load_llm_config(raw=True)
    masked = dict(raw)
    key = masked.get("api_key", "")
    masked["api_key"] = ""
    masked["has_key"] = bool(key)
    if key:
        masked["key_hint"] = key[:4] + "…" + key[-4:] if len(key) > 8 else "已配置"
    else:
        masked["key_hint"] = ""
    return {"ok": True, "data": masked}


@app.post("/api/llm-config/test")
async def test_llm_config(request: Request):
    raw = await request.body()
    req = json.loads(raw) if raw else {}
    cfg = {**_load_llm_config(raw=True), **req}
    if cfg.get("api_key") in ("", "__KEEP__"):
        cfg["api_key"] = _load_llm_config(raw=True).get("api_key", "")
    client = _build_llm(cfg)
    if not client:
        raise HTTPException(400, "无法连接：未配置 API Key")
    try:
        reply = client.complete("回复 OK 两个字母即可。")
        return {"ok": True, "data": {"reply": (reply or "")[:120]}}
    except Exception as e:
        raise HTTPException(502, f"连接失败: {e}") from e


@app.put("/api/llm-config")
async def update_llm_config(request: Request):
    req = await _parse_json_body(request)
    current = _load_llm_config(raw=True)
    provider = req.get("provider", current.get("provider", "deepseek"))
    api_key = req.get("api_key", "")
    if api_key in ("", "__KEEP__"):
        api_key = current.get("api_key", "")
    data = {
        "provider": provider,
        "api_key": api_key,
        "base_url": req.get("base_url", current.get("base_url", "")),
        "model": req.get("model", current.get("model", "")),
    }
    _save_llm_config(data)
    return {"ok": True}


@app.get("/api/style")
async def get_style():
    return {"ok": True, "data": load_style()}


@app.put("/api/style")
async def update_style(request: Request):
    req = await _parse_json_body(request)
    (DATA_DIR / "style.json").write_text(
        json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"ok": True}


@app.get("/api/sensitive-words")
async def get_sensitive_words():
    from core.data_loader import load_sensitive_words
    return {"ok": True, "data": load_sensitive_words()}


@app.put("/api/sensitive-words")
async def update_sensitive_words(request: Request):
    req = await _parse_json_body(request)
    (DATA_DIR / "sensitive_words.json").write_text(
        json.dumps(req, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return {"ok": True}


# ── Check ──────────────────────────────────────────────────
@app.post("/api/check")
async def check_text(request: Request):
    req = await _parse_json_body(request)
    text = req.get("text", "")
    local_safe, local_violations = anti_detect.validate(text)
    ad_safe, ad_violations = get_ad_law_checker().validate(text)
    sanitized = anti_detect.sanitize(text)
    overall_safe = local_safe and ad_safe
    return {
        "ok": True,
        "safe": overall_safe,
        "violations": local_violations,
        "sanitized": sanitized,
        "changed": sanitized != text,
        "layers": {
            "local": {
                "label": "本地·闲鱼词库",
                "safe": local_safe,
                "violations": local_violations,
            },
            "ad_law": {
                "label": "参考·广告法极限词",
                "hint": "词表参考 UU 工具公开规则，本地匹配，非官网实时接口",
                "safe": ad_safe,
                "violations": ad_violations,
            },
        },
    }


# ── Export ─────────────────────────────────────────────────
@app.post("/api/export")
async def export_copy(request: Request):
    req = await _parse_json_body(request)
    variants = req.get("variants", [])
    fmt = req.get("format", "txt")
    if fmt == "json":
        content = json.dumps(variants, ensure_ascii=False, indent=2)
        return {"ok": True, "content": content}
    lines = []
    for i, v in enumerate(variants):
        lines.append(f"=== {v.get('version', f'V{i+1}')} ===")
        lines.append(f"标题: {v.get('title', '')}")
        tags = v.get("tags") or []
        if tags:
            lines.append(f"标签: {' '.join(tags)}")
        lines.append(f"{v.get('body', '')}")
        lines.append("")
    return {"ok": True, "content": "\n".join(lines)}


# ── Helpers ────────────────────────────────────────────────
def _apply_generate_style(gen: CopyGenerator, style: str | None, version_count: int, multi_style: bool):
    """Configure variant styles for generate requests.

    - multi_style=True: use preset variants from style.json (standard / concise / case-led)
    - version_count=1 + style: single variant with the chosen style
    - version_count>1 + style (no multi_style): N variants sharing the same style
    """
    preset = dict(gen.style.get("variants") or {})
    if not preset:
        preset = load_style().get("variants", {})

    if multi_style or (not style and version_count > 1):
        keys = list(preset.keys())[: max(1, min(version_count, len(preset)))]
        gen.style["version_count"] = len(keys)
        gen.style["variants"] = {k: preset[k] for k in keys}
        return

    if style and version_count <= 1:
        gen.style["version_count"] = 1
        gen.style["variants"] = {
            "v_custom": {"description": "自定义风格", "style": style}
        }
        return

    if style and version_count > 1:
        gen.style["version_count"] = version_count
        gen.style["variants"] = {
            f"v{i + 1}": {"description": f"版本{i + 1}", "style": style}
            for i in range(version_count)
        }
        return

    gen.style["version_count"] = max(1, min(version_count, len(preset) or version_count))
    if preset:
        keys = list(preset.keys())[: gen.style["version_count"]]
        gen.style["variants"] = {k: preset[k] for k in keys}


def _history_row_to_dict(r) -> dict:
    meta = {}
    try:
        meta = json.loads(r["meta"]) if r["meta"] else {}
    except (json.JSONDecodeError, TypeError):
        pass
    variants = json.loads(r["variants"])
    return {
        "id": r["id"],
        "keywords": json.loads(r["keywords"]),
        "style": r["style"],
        "variants": variants,
        "meta": meta,
        "variant_count": len(variants),
        "created_at": r["created_at"],
    }


def _save_history(keywords, style, variants, meta=None) -> int:
    with connect() as db:
        cur = db.execute(
            "INSERT INTO history (keywords, style, variants, meta, created_at) VALUES (?, ?, ?, ?, ?)",
            (
                json.dumps(keywords, ensure_ascii=False),
                style,
                json.dumps(variants, ensure_ascii=False),
                json.dumps(meta or {}, ensure_ascii=False),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        return cur.lastrowid


async def _parse_json_body(request: Request) -> dict:
    body = await request.body()
    if not body:
        raise HTTPException(400, "empty body")
    try:
        return json.loads(body)
    except json.JSONDecodeError as e:
        raise HTTPException(400, f"invalid JSON: {e}") from e


def _load_llm_config(*, raw: bool = False) -> dict:
    if LLM_CONFIG_PATH.exists():
        try:
            data = json.loads(LLM_CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
    return {
        "provider": "deepseek",
        "api_key": "",
        "base_url": "",
        "model": "",
    }


def _save_llm_config(data: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LLM_CONFIG_PATH.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def _build_llm(cfg: dict):
    provider = cfg.get("provider", "")
    api_key = cfg.get("api_key", "")
    base_url = cfg.get("base_url", "")
    model = cfg.get("model", "")
    presets = {
        "deepseek": ("https://api.deepseek.com/v1", "deepseek-chat"),
        "qwen": ("https://dashscope.aliyuncs.com/compatible-mode/v1", "qwen-plus"),
        "openai": ("https://api.openai.com/v1", "gpt-4o"),
    }
    preset = presets.get(provider, ("", ""))
    base_url = base_url or preset[0]
    model = model or preset[1]
    if not api_key:
        api_key = _load_llm_config(raw=True).get("api_key", "")
    api_key = api_key or _env_key(provider)
    if not api_key:
        return None
    return OpenAICompat(api_key=api_key, base_url=base_url, model=model)


def _env_key(provider: str) -> str:
    import os
    return os.environ.get({
        "deepseek": "DEEPSEEK_API_KEY", "qwen": "DASHSCOPE_API_KEY",
        "openai": "OPENAI_API_KEY",
    }.get(provider, ""))


# ── SPA fallback (must be last) ────────────────────────────
@app.get("/{full_path:path}")
async def spa_fallback(full_path: str):
    if full_path.startswith("api"):
        raise HTTPException(404)
    if _vue_built():
        asset = DIST / full_path
        if asset.is_file():
            return FileResponse(str(asset.resolve()))
        return _html_file(DIST / "index.html")
    return _html_file(_spa_index_path())


# ── Main ───────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8765, reload=True)
