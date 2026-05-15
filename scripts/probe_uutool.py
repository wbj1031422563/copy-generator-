import re
import urllib.request

req = urllib.request.Request(
    "https://uutool.cn/check-word/",
    headers={"User-Agent": "Mozilla/5.0"},
)
html = urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "ignore")
for kw in ["dataResource", "tool-box", "toolBox", "check-word", "wjc", "api/"]:
    print(kw, html.count(kw))
srcs = re.findall(r'src="([^"]+)"', html)
print("scripts", len(srcs))
for s in srcs[:20]:
    print(" ", s[:100])
