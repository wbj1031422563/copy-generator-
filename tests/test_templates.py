"""Basic tests for copy templates."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_loader import load_profile, load_services
from core.templates import build_body, build_tags, build_title


def test_build_title_length():
    services = load_services()
    profile = load_profile()
    title = build_title(["目标检测", "YOLO"], services, profile, style="comprehensive")
    assert len(title) <= 30


def test_build_body_has_identity():
    services = load_services()
    profile = load_profile()
    body = build_body(["深度学习"], services, profile)
    assert profile["identity"][:4] in body or "本人" in body


def test_build_tags_dedup():
    services = load_services()
    tags = build_tags(["YOLO", "深度学习", "YOLO"], services, max_count=5)
    assert len(tags) == len(set(tags))
    assert len(tags) <= 5


if __name__ == "__main__":
    test_build_title_length()
    test_build_body_has_identity()
    test_build_tags_dedup()
    print("ok")
