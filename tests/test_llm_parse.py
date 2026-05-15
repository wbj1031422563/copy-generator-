"""Tests for LLM response parsing."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_parse import parse_copy_response


def test_parse_title_body_labels():
    text = """TITLE: 目标检测 YOLO 博士指导
BODY: 本人北邮博士，成果丰富。

主攻计算机视觉方向。"""
    title, body = parse_copy_response(text)
    assert "YOLO" in title
    assert len(title) <= 30
    assert "北邮" in body


def test_parse_chinese_labels():
    text = "标题：深度学习 论文指导\n详情：本人博士，提供思路与会议辅导。"
    title, body = parse_copy_response(text)
    assert title
    assert "博士" in body


def test_parse_json():
    text = '{"title": "NLP大模型辅导", "body": "主攻NLP与大模型，欢迎私聊。"}'
    title, body = parse_copy_response(text)
    assert "NLP" in title
    assert "私聊" in body
