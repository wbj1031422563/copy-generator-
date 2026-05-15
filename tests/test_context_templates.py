"""Tests for generation context and enhanced templates."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.context import build_generation_context
from core.data_loader import load_profile, load_services
from core.templates import (
    _match_cross_fields,
    _pick_conferences,
    build_body,
    build_title,
)


def test_cross_fields_medical():
    services = load_services()
    cross = _match_cross_fields(services, ["医学图像", "分割"])
    assert any("医学" in c for c in cross)


def test_conferences_nlp_hint():
    services = load_services()
    confs = _pick_conferences(services, ["NLP", "大模型"])
    assert "ACL" in confs or "EMNLP" in confs


def test_build_body_min_length():
    services = load_services()
    profile = load_profile()
    body = build_body(["YOLO", "目标检测"], services, profile, style="comprehensive")
    assert len(body) >= 280


def test_title_differs_by_style():
    services = load_services()
    profile = load_profile()
    kws = ["医学图像", "人工智能"]
    t1 = build_title(kws, services, profile, style="comprehensive")
    t2 = build_title(kws, services, profile, style="case_led")
    assert len(t1) <= 30
    assert len(t2) <= 30


def test_context_has_examples():
    ctx = build_generation_context(["深度学习"], "comprehensive")
    assert ctx["domains"]
    assert ctx["must_avoid"]
    assert "examples_excerpt" in ctx
