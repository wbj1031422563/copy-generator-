"""细粒度功能检测：各子模块 CRUD 与页面路由。"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"
results: list[tuple[str, str, bool, str]] = []


def call(method: str, path: str, body: dict | None = None, timeout: int = 60):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(
        BASE + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, {"_raw_len": len(raw)}
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode())
        except Exception:
            detail = {"detail": e.reason}
        return e.code, detail
    except Exception as e:
        return "ERR", {"detail": str(e)}


def record(module: str, name: str, ok: bool, note: str = ""):
    results.append((module, name, ok, note))


def ok(st, j, allow_no_data: bool = False) -> bool:
    if st != 200:
        return False
    if isinstance(j, dict) and j.get("ok") is False:
        return False
    if not allow_no_data and isinstance(j, dict) and "data" in j and j["data"] is None:
        return False
    return True


def main() -> int:
    # ── 1. 基础与前端 ─────────────────────────────
    st, j = call("GET", "/api/health")
    record("基础", "健康检查", ok(st, j), str(j.get("data", {}))[:80])

    st, j = call("GET", "/")
    record("基础", "首页 HTML", st == 200 and isinstance(j, dict) and j.get("_raw_len", 0) > 100)

    for route in [
        "/dashboard",
        "/generate/chat",
        "/generate/batch",
        "/keywords",
        "/history",
        "/templates",
        "/export",
        "/tools/checker",
        "/settings/profile",
        "/settings/llm",
        "/help",
        "/chat",
        "/batch",
        "/checker",
    ]:
        st, j = call("GET", route)
        record("前端路由", route, st == 200)

    # ── 2. 对话生成（多版本 / 多风格）──────────────
    st, j = call(
        "POST",
        "/api/generate",
        {
            "keywords": ["YOLO", "目标检测"],
            "version_count": 3,
            "multi_style": True,
            "use_llm": False,
        },
        60,
    )
    vcount = len(j.get("data", {}).get("variants", [])) if ok(st, j) else 0
    record("对话生成", "三版本多风格(模板)", ok(st, j) and vcount == 3, f"variants={vcount}")

    st, j = call(
        "POST",
        "/api/generate",
        {
            "keywords": ["论文润色"],
            "version_count": 1,
            "style": "concise_casual",
            "use_llm": False,
        },
        60,
    )
    record("对话生成", "简洁版单条", ok(st, j))

    st, j = call(
        "POST",
        "/api/generate",
        {
            "keywords": ["SCI"],
            "version_count": 1,
            "style": "case_led",
            "use_llm": False,
        },
        60,
    )
    record("对话生成", "案例版单条", ok(st, j))

    st, j = call(
        "POST",
        "/api/generate",
        {
            "keywords": ["深度学习"],
            "version_count": 1,
            "use_llm": True,
            "llm": {"provider": "deepseek"},
        },
        120,
    )
    llm_used = j.get("data", {}).get("llm_used") if isinstance(j, dict) else False
    record("对话生成", "AI 生成", ok(st, j) and llm_used, f"llm_used={llm_used}")

    # ── 3. 批量生成 ───────────────────────────────
    st, j = call(
        "POST",
        "/api/generate-batch",
        {
            "keyword_sets": [["CV", "分割"], ["NLP", "大模型"]],
            "style": "comprehensive",
            "use_llm": False,
        },
        90,
    )
    n = len(j.get("data", {}).get("results", [])) if ok(st, j) else 0
    record("批量生成", "两组关键词", ok(st, j) and n == 2, f"results={n}")

    # ── 4. 合规检测 ───────────────────────────────
    st, j = call("POST", "/api/check", {"text": "包过 代写 枪手"})
    record("合规检测", "违禁词检测", ok(st, j), f"safe={j.get('safe')}")

    st, j = call("POST", "/api/check", {"text": "深度学习辅导 正常文案"})
    record("合规检测", "正常文案", ok(st, j) and j.get("safe") is True)

    # ── 5. 导出 ───────────────────────────────────
    st, j = call(
        "POST",
        "/api/export",
        {
            "variants": [{"title": "T", "body": "B", "tags": ["a", "b"]}],
            "format": "txt",
        },
    )
    record("导出", "TXT 格式", ok(st, j) and bool(j.get("content")))

    st, j = call(
        "POST",
        "/api/export",
        {
            "variants": [{"title": "T", "body": "B"}],
            "format": "json",
        },
    )
    record("导出", "JSON 格式", ok(st, j) and bool(j.get("content")))

    # ── 6. 历史记录 CRUD ──────────────────────────
    st, j = call("GET", "/api/history?limit=1")
    hid = None
    if ok(st, j) and j.get("data"):
        hid = j["data"][0]["id"]
    record("历史", "列表读取", ok(st, j), f"id={hid}")

    if hid:
        st, j = call("GET", f"/api/history/{hid}")
        record("历史", "单条详情", ok(st, j))

        qs = urllib.parse.urlencode({"search": "YOLO", "limit": "10"})
        st, j = call("GET", f"/api/history?{qs}")
        search_ok = ok(st, j) and isinstance(j.get("data"), list)
        record("历史", "关键词搜索", search_ok, f"hits={len(j.get('data', []))}")

        st2, j2 = call("GET", f"/api/history/{hid}")
        item = j2.get("data") if ok(st2, j2) and isinstance(j2.get("data"), dict) else {}
        variants = item.get("variants", [])
        st, j = call("PUT", f"/api/history/{hid}", {"variants": variants})
        record("历史", "更新记录", ok(st, j))

    # 创建一条用于删除测试
    st, j = call(
        "POST",
        "/api/generate",
        {"keywords": ["_delete_test_"], "version_count": 1, "use_llm": False},
        60,
    )
    del_id = j.get("data", {}).get("history_id") if ok(st, j) else None
    if del_id:
        st, j = call("DELETE", f"/api/history/{del_id}")
        record("历史", "删除单条", ok(st, j))
        st, j = call("GET", f"/api/history/{del_id}")
        record("历史", "删除后不可见", st == 404 or (isinstance(j, dict) and "not found" in str(j.get("detail", "")).lower()))

    # ── 7. 文案模板 CRUD ──────────────────────────
    tpl_name = "_smoke_tpl_"
    call("DELETE", f"/api/templates/{tpl_name}")
    st, j = call(
        "POST",
        "/api/templates",
        {"name": tpl_name, "content": "测试模板内容 {{keywords}}"},
    )
    record("模板", "新建", ok(st, j))

    st, j = call("GET", "/api/templates")
    found = any(t.get("name") == tpl_name for t in (j.get("data") or [])) if ok(st, j) else False
    record("模板", "列表含新建", ok(st, j) and found)

    st, j = call("PUT", f"/api/templates/{tpl_name}", {"content": "已更新内容"})
    record("模板", "编辑保存", ok(st, j))

    st, j = call("DELETE", f"/api/templates/{tpl_name}")
    record("模板", "删除", ok(st, j))

    # ── 8. 优质范例 CRUD ──────────────────────────
    st, j = call(
        "POST",
        "/api/good-copies",
        {
            "keywords": ["测试"],
            "title": "测试标题",
            "body": "测试正文内容",
            "style": "comprehensive",
        },
    )
    gid = j.get("data", {}).get("id") if ok(st, j) else None
    record("优质范例", "收藏", ok(st, j) and gid is not None, f"id={gid}")

    if gid:
        st, j = call("GET", "/api/good-copies")
        has = any(x.get("id") == gid for x in (j.get("data") or []))
        record("优质范例", "列表可见", ok(st, j) and has)

        st, j = call("DELETE", f"/api/good-copies/{gid}")
        record("优质范例", "删除", ok(st, j))

    # ── 9. 设置读写 ───────────────────────────────
    st, j = call("GET", "/api/profile")
    profile = j.get("data", {}) if ok(st, j) else {}
    profile["extra"] = (profile.get("extra") or "") + ""
    st, j = call("PUT", "/api/profile", profile)
    record("设置", "人设保存", ok(st, j))

    st, j = call("GET", "/api/services")
    record("设置", "服务项目读取", ok(st, j))

    st, j = call("GET", "/api/style")
    record("设置", "风格配置读取", ok(st, j))

    st, j = call("GET", "/api/sensitive-words")
    record("设置", "敏感词库读取", ok(st, j))

    st, j = call("PUT", "/api/llm-config", {"provider": "deepseek", "api_key": "__KEEP__"})
    record("设置", "LLM 配置保存", ok(st, j))

    st, j = call("POST", "/api/llm-config/test", {"provider": "deepseek", "api_key": "__KEEP__"}, 90)
    reply = j.get("data", {}).get("reply", "") if ok(st, j) else ""
    record("设置", "LLM 测试连接", ok(st, j) and bool(reply), f"reply={reply[:30]}")

    # ── 10. 关键词库 ──────────────────────────────
    st, j = call("GET", "/api/keywords")
    domains = j.get("data", {}).get("domains", []) if ok(st, j) else []
    record("关键词库", "领域列表", ok(st, j) and len(domains) > 0, f"domains={len(domains)}")

    # ── 11. 工作台 ────────────────────────────────
    st, j = call("GET", "/api/dashboard")
    d = j.get("data", {}) if ok(st, j) else {}
    record("工作台", "概览数据", ok(st, j) and "total_generations" in d)

    st, j = call("GET", "/api/stats")
    record("工作台", "侧栏统计", ok(st, j))

    # ── 输出 ────────────────────────────────────
    by_module: dict[str, list] = {}
    for mod, name, passed, note in results:
        by_module.setdefault(mod, []).append((name, passed, note))

    print("=" * 60)
    print(f"功能细项检测 @ {BASE}")
    print("=" * 60)
    total_pass = 0
    for mod, items in by_module.items():
        print(f"\n【{mod}】")
        for name, passed, note in items:
            mark = "OK" if passed else "FAIL"
            extra = f"  ({note})" if note else ""
            print(f"  {mark} {name}{extra}")
            if passed:
                total_pass += 1
    print(f"\n{'=' * 60}")
    print(f"合计: {total_pass}/{len(results)} 通过")
    failed = [(m, n, note) for m, n, p, note in results if not p]
    if failed:
        print("\n未通过项:")
        for m, n, note in failed:
            print(f"  - [{m}] {n}: {note}")
    return 0 if total_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
