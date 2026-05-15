import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.ad_law_check import get_ad_law_checker


def test_ad_law_detects_limit_word():
    checker = get_ad_law_checker()
    safe, violations = checker.validate("这是国家级产品，全网第一")
    assert safe is False
    assert "国家级" in violations or "全网第一" in violations


def test_ad_law_passes_normal_text():
    checker = get_ad_law_checker()
    safe, violations = checker.validate("深度学习论文辅导，欢迎私聊")
    assert safe is True
    assert violations == []
