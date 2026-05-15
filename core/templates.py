"""Copy templates for academic tutoring product listings on Xianyu."""

from __future__ import annotations


def build_title(
    keywords: list[str],
    services: dict,
    profile: dict,
    style: str = "comprehensive",
) -> str:
    """Generate a title (≤30 chars) with keywords front-loaded."""
    kw_str = "".join(keywords[:2]) if style == "concise_casual" else " ".join(keywords[:3])
    domain = _pick_domain(services, keywords)
    cross = _match_cross_fields(services, keywords)

    templates: list[str]
    if style == "case_led" and cross:
        templates = [
            f"{cross[0]} {keywords[0]} 指导" if keywords else f"{cross[0]} 论文指导",
            f"{domain}交叉学科 博士辅导",
        ]
    elif style == "concise_casual":
        templates = [
            f"{kw_str} 博士辅导",
            f"{domain} 论文指导",
            f"{keywords[0]} 科研支持" if keywords else f"{domain} 科研支持",
        ]
    else:
        templates = [
            f"{kw_str} 指导",
            f"{domain}方向 论文指导",
            f"{kw_str}思路idea",
            f"{domain} 科研支持",
            f"{domain}论文 全程指导",
            f"{kw_str} 博士指导",
        ]

    for t in templates:
        t = t.strip()
        if t and len(t) <= 30:
            return t
    return (templates[0] if templates else "学术辅导")[:30]


def build_tags(keywords: list[str], services: dict, max_count: int = 9) -> list[str]:
    """Pick Xianyu listing tags from keywords + defaults (deduped, capped)."""
    defaults = services.get("default_tags", [])
    seen: set[str] = set()
    tags: list[str] = []
    for w in keywords + defaults:
        w = (w or "").strip()
        if not w or w in seen:
            continue
        seen.add(w)
        tags.append(w)
        if len(tags) >= max_count:
            break
    return tags


def build_body(
    keywords: list[str],
    services: dict,
    profile: dict,
    style: str = "comprehensive",
) -> str:
    """Build the listing body (target 300-500 chars)."""
    identity = profile.get("identity", "")
    roles = "、".join(profile.get("role_tags", []))
    highlight = profile.get("highlight", "")
    contact = profile.get("contact", "")
    extra = profile.get("extra", "")
    audience = profile.get("audience", [])

    matched_domains = _match_domains(services, keywords)
    topic_kws = _match_topic_keywords(services, keywords)
    cross = _match_cross_fields(services, keywords)
    matched_types = _pick_service_types(services, style)
    levels = _pick_levels(services)
    confs = _pick_conferences(services, keywords)

    sections: list[str] = []

    if style == "case_led" and extra:
        sections.append(f"近期辅导：{extra}")

    sections.append(f"本人{identity}，{roles}")

    if cross:
        sections.append(f"交叉方向：{'、'.join(cross)}")

    if matched_domains:
        domains_str = "、".join(matched_domains[:6])
        sections.append(f"主攻方向：{domains_str}")

    if topic_kws and style == "comprehensive":
        sections.append(f"技术覆盖：{'、'.join(topic_kws[:10])}")

    if extra and style != "case_led":
        sections.append(extra)

    if confs and style != "concise_casual":
        conf_str = "、".join(confs[:6])
        sections.append(f"可辅导{conf_str}等会议/期刊，层次含{levels}")

    if matched_types:
        types_str = "\n".join(f"- {t}" for t in matched_types[:5 if style == "comprehensive" else 3])
        sections.append(f"服务内容：\n{types_str}")

    if audience:
        n = 4 if style == "comprehensive" else 2
        sections.append(f"适合{'、'.join(audience[:n])}")

    sections.append(f"{highlight}。{contact}")

    body = "\n\n".join(sections)
    max_len = 500 if style != "concise_casual" else 400
    body = body[:max_len]

    if len(body) < 280 and style != "concise_casual":
        body = _pad_body(body, topic_kws, matched_domains, max_len)

    return body


def _pad_body(body: str, topic_kws: list[str], domains: list[str], max_len: int) -> str:
    """Add relevant technical keywords if body is too short."""
    extras = [k for k in topic_kws if k not in body][:8]
    if extras:
        body = body + f"\n\n相关技术：{'、'.join(extras)}。"
    if len(body) < 280 and domains:
        body = body + f"\n\n长期深耕{'、'.join(domains[:3])}方向，欢迎带具体问题私聊。"
    return body[:max_len]


def _match_domains(services: dict, keywords: list[str]) -> list[str]:
    domains = services.get("domains", [])
    matched: set[str] = set()
    for d in domains:
        name = d.get("name", "")
        for kw in keywords:
            if kw.lower() in name.lower() or name.lower() in kw.lower():
                matched.add(name)
                break
    for d in domains:
        for topic_kw in d.get("keywords", []):
            for kw in keywords:
                if kw.lower() in topic_kw.lower() or topic_kw.lower() in kw.lower():
                    matched.add(d.get("name", ""))
    return list(matched) or [d["name"] for d in domains[:3]]


def _match_topic_keywords(services: dict, keywords: list[str]) -> list[str]:
    """Collect domain topic keywords that match user keywords."""
    hits: list[str] = []
    seen: set[str] = set()
    user = [k.lower() for k in keywords]

    for d in services.get("domains", []):
        for topic_kw in d.get("keywords", []):
            tl = topic_kw.lower()
            if any(u in tl or tl in u for u in user):
                if topic_kw not in seen:
                    seen.add(topic_kw)
                    hits.append(topic_kw)

    for kw in keywords:
        if kw not in seen and len(kw) >= 2:
            seen.add(kw)
            hits.append(kw)

    return hits[:15]


def _match_cross_fields(services: dict, keywords: list[str]) -> list[str]:
    cross = services.get("cross_fields", [])
    if not cross:
        return []
    user_text = " ".join(keywords)
    mapping = {
        "医学": "医学",
        "医疗": "医学",
        "农业": "农业",
        "地理": "地理",
        "教育": "教育",
    }
    matched: list[str] = []
    for token, label in mapping.items():
        if token in user_text:
            for field in cross:
                if label in field and field not in matched:
                    matched.append(field)
    if "交叉" in user_text and not matched:
        matched = cross[:2]
    return matched


def _pick_domain(services: dict, keywords: list[str]) -> str:
    matched = _match_domains(services, keywords)
    return matched[0] if matched else "深度学习"


def _pick_service_types(services: dict, style: str) -> list[str]:
    all_types = services.get("service_types", [])
    if not all_types:
        return []
    if style == "concise_casual":
        return all_types[:3]
    if style == "case_led":
        picks = [all_types[0]]
        if len(all_types) > 2:
            picks.append(all_types[2])
        if len(all_types) > 1:
            picks.append(all_types[-1])
        return picks
    return all_types[:5]


def _pick_levels(services: dict) -> str:
    levels = services.get("levels", [])
    return "、".join(levels[:5])


def _pick_conferences(services: dict, keywords: list[str]) -> list[str]:
    all_confs = services.get("featured_conferences", [])
    if not all_confs:
        return []

    user = " ".join(keywords).upper()
    tier_a = {"CVPR", "ICCV", "ECCV", "NEURIPS", "ICML", "ICLR", "AAAI", "IJCAI", "ACL", "EMNLP"}
    matched = [c for c in all_confs if c.upper() in user or c.upper().replace(" ", "") in user.replace(" ", "")]

    if not matched:
        if any(k in user for k in ("NLP", "LLM", "大模型", "语言")):
            matched = [c for c in all_confs if c in ("ACL", "EMNLP", "AAAI", "IJCAI", "NeurIPS", "ICLR")]
        elif any(k in user for k in ("CV", "视觉", "检测", "YOLO", "图像", "分割")):
            matched = [c for c in all_confs if c in ("CVPR", "ICCV", "ECCV", "AAAI", "IJCAI", "ICIP", "WACV")]

    if not matched:
        matched = [c for c in all_confs if c in tier_a][:6]
    if not matched:
        matched = all_confs[:6]

    seen: set[str] = set()
    out: list[str] = []
    for c in matched + all_confs:
        if c not in seen:
            seen.add(c)
            out.append(c)
        if len(out) >= 8:
            break
    return out
