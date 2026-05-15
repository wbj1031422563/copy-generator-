"""广告法 / 极限词参考检测（词表参考 UU 工具公开说明，本地匹配，非官网实时 API）。"""

from __future__ import annotations

from core.data_loader import load_sensitive_words


class AdLawChecker:
    """参考电商广告法常见极限词、绝对化用语（与 uutool.cn/check-word 公开分类一致方向）。"""

    def __init__(self) -> None:
        rules = load_sensitive_words()
        self.limits: list[str] = list(rules.get("ad_law_limits", []))

    def validate(self, text: str) -> tuple[bool, list[str]]:
        violations: list[str] = []
        lower = text.lower()
        seen: set[str] = set()
        for word in self.limits:
            w = word.strip()
            if not w or w in seen:
                continue
            if w.lower() in lower or w in text:
                violations.append(w)
                seen.add(w)
        return len(violations) == 0, violations


_ad_law_checker: AdLawChecker | None = None


def get_ad_law_checker() -> AdLawChecker:
    global _ad_law_checker
    if _ad_law_checker is None:
        _ad_law_checker = AdLawChecker()
    return _ad_law_checker
