"""Quick smoke test for copy-generator API (run server on 8765 first)."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8765"


def req(method: str, path: str, body: dict | None = None, timeout: int = 60):
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
                j = json.loads(raw)
            except json.JSONDecodeError:
                j = {"_raw_len": len(raw)}
            return resp.status, j
    except urllib.error.HTTPError as e:
        return e.code, {"detail": e.read().decode()[:300]}
    except Exception as e:
        return "ERR", {"detail": str(e)}


def ok_status(st, j) -> bool:
    if st != 200:
        return False
    if isinstance(j, dict) and j.get("ok") is False:
        return False
    return True


def summarize(j) -> str:
    if not isinstance(j, dict):
        return ""
    if "data" in j and isinstance(j["data"], dict):
        d = j["data"]
        parts = []
        for k in ("status", "frontend", "variants", "results", "reply", "llm_used"):
            if k in d:
                v = d[k]
                if k == "variants" and isinstance(v, list):
                    parts.append(f"variants={len(v)}")
                elif k == "results" and isinstance(v, list):
                    parts.append(f"batch={len(v)}")
                elif k == "reply":
                    parts.append(f"reply={str(v)[:40]}")
                else:
                    parts.append(f"{k}={v}")
        return " ".join(parts)
    if "safe" in j:
        return f"safe={j['safe']}"
    if "content" in j:
        return "export_len=" + str(len(j.get("content", "")))
    if "detail" in j:
        return str(j["detail"])[:60]
    return ""


checks: list[tuple[str, str, dict | None, int]] = [
    ("GET", "/api/health", None, 20),
    ("GET", "/", None, 20),
    ("GET", "/assets/index-fTABZ8QS.js", None, 20),
    ("GET", "/api/dashboard", None, 20),
    ("GET", "/api/stats", None, 20),
    ("GET", "/api/llm-config", None, 20),
    ("GET", "/api/profile", None, 20),
    ("GET", "/api/services", None, 20),
    ("GET", "/api/style", None, 20),
    ("GET", "/api/sensitive-words", None, 20),
    ("GET", "/api/keywords", None, 20),
    ("GET", "/api/templates", None, 20),
    ("GET", "/api/history?limit=3", None, 20),
    ("GET", "/api/good-copies", None, 20),
    ("GET", "/api/db-status", None, 20),
    (
        "POST",
        "/api/generate",
        {
            "keywords": ["测试", "深度学习"],
            "version_count": 1,
            "style": "comprehensive",
            "use_llm": False,
        },
        60,
    ),
    (
        "POST",
        "/api/generate-batch",
        {"keyword_sets": [["NLP"]], "style": "comprehensive", "use_llm": False},
        60,
    ),
    ("POST", "/api/check", {"text": "深度学习论文辅导"}, 20),
    (
        "POST",
        "/api/export",
        {"variants": [{"title": "标题", "body": "正文", "tags": ["标签"]}], "format": "txt"},
        20,
    ),
    ("POST", "/api/llm-config/test", {"provider": "deepseek", "api_key": "__KEEP__"}, 90),
    (
        "POST",
        "/api/generate",
        {
            "keywords": ["深度学习"],
            "version_count": 1,
            "style": "comprehensive",
            "use_llm": True,
            "llm": {"provider": "deepseek"},
        },
        120,
    ),
]

passed = 0
for method, path, body, timeout in checks:
    st, j = req(method, path, body, timeout)
    good = ok_status(st, j)
    if good:
        passed += 1
    mark = "PASS" if good else "FAIL"
    print(f"{mark} {method:4} {path:35} {st!s:>4}  {summarize(j)}")

print(f"\nTotal: {passed}/{len(checks)} passed")
sys.exit(0 if passed == len(checks) else 1)
