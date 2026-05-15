"""Assemble structured context for copy generation (template + LLM)."""

from __future__ import annotations

from core.data_loader import load_copy_examples, load_profile, load_services, load_sensitive_words

try:
    from core.database import load_good_examples_for_prompt
except Exception:
    def load_good_examples_for_prompt(limit: int = 3, max_chars: int = 1500) -> str:
        return ""
from core.templates import (
    _match_cross_fields,
    _match_domains,
    _match_topic_keywords,
    _pick_conferences,
    _pick_levels,
    _pick_service_types,
)


STYLE_HINTS = {
    "comprehensive": "标准版：完整列举技术方向、会议/期刊级别、服务内容，专业真诚，300-500字。",
    "concise_casual": "简洁版：保留核心方向与服务，口语化、段落更短，250-380字。",
    "case_led": "案例版：开头用成果或交叉学科辅导案例吸引注意，再写方向与服务，300-480字。",
}


def build_generation_context(keywords: list[str], variant_style: str = "comprehensive") -> dict:
    """Build a dict passed to template engine and LLM prompts."""
    profile = load_profile()
    services = load_services()
    sensitive = load_sensitive_words()

    domains = _match_domains(services, keywords)
    topic_kws = _match_topic_keywords(services, keywords)
    cross = _match_cross_fields(services, keywords)
    confs = _pick_conferences(services, keywords)
    levels = _pick_levels(services)
    service_types = _pick_service_types(services, variant_style)

    file_examples = load_copy_examples(max_chars=1200)
    db_examples = load_good_examples_for_prompt(limit=3, max_chars=1200)
    examples_parts = [p for p in (db_examples, file_examples) if p]
    examples_excerpt = "\n\n".join(examples_parts)[:2400]

    return {
        "keywords": keywords,
        "variant_style": variant_style,
        "style_hint": STYLE_HINTS.get(variant_style, STYLE_HINTS["comprehensive"]),
        "profile": profile,
        "services": services,
        "domains": domains,
        "topic_keywords": topic_kws,
        "cross_fields": cross,
        "conferences": confs,
        "levels": levels,
        "service_types": service_types,
        "must_avoid": sensitive.get("must_avoid", []),
        "examples_excerpt": examples_excerpt,
        "has_good_examples": bool(db_examples),
    }
