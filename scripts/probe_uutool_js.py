import re
import urllib.request

urls = [
    "https://uutool.cn/assets/js/tools/check-word.js?v=1770962344",
    "https://nbcdn.qikekeji.com/webres/uutool/tools/check-word.js",
]
for u in urls:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        js = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
        print("OK", u, "len", len(js))
        for pat in ["dataResource", "api", "fetch", "axios", "check", "wjc", "post"]:
            if pat in js:
                print(" ", pat, js.count(pat))
        for m in re.finditer(r"['\"](/[^'\"]{5,80})['\"]", js):
            p = m.group(1)
            if any(x in p for x in ("api", "check", "word", "wjc")):
                print(" path", p)
        break
    except Exception as e:
        print("fail", u, type(e).__name__, e)
