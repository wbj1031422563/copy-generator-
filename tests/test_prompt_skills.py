"""Prompt skills assembly tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.anti_detect import AntiDetect
from core.prompt_builder import build_system_prompt, build_user_prompt
from core.prompt_skills import assemble_generation_skills, skill_xianyu_compliance


def test_skills_contain_compliance():
    block = skill_xianyu_compliance(["代写", "包过"])
    assert "代写" in block
    assert "闲鱼合规" in block


def test_assemble_has_four_skills():
    block = assemble_generation_skills({"variant_style": "comprehensive", "must_avoid": ["代写"]})
    assert "闲鱼合规" in block
    assert "去 AI 腔" in block
    assert "闲鱼结构" in block
    assert "输出前自检" in block


def test_system_prompt_has_skills():
    s = build_system_prompt()
    assert "TITLE" in s or "合规" in s


def test_user_prompt_includes_skills_block():
    ctx = {
        "profile": {"identity": "博士", "role_tags": [], "audience": [], "highlight": "", "contact": "", "extra": ""},
        "domains": ["CV"],
        "topic_keywords": ["YOLO"],
        "cross_fields": [],
        "conferences": ["CVPR"],
        "levels": "SCI",
        "service_types": ["指导"],
        "keywords": ["YOLO"],
        "must_avoid": ["代写"],
        "examples_excerpt": "",
        "style_hint": "标准",
        "variant_style": "comprehensive",
        "has_good_examples": False,
    }
    p = build_user_prompt(ctx, "标题", "正文")
    assert "技能·闲鱼合规" in p


def test_soft_detect():
    ad = AntiDetect()
    hits = ad.detect_soft_risks("综上所述，我们团队赋能您的科研")
    assert "综上所述" in hits
