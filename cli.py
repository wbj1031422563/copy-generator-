#!/usr/bin/env python3
"""Copy Generator CLI — 闲鱼学术辅导文案生成器.

Usage:
    uv run python cli.py "目标检测" "YOLO" "计算机视觉"
    uv run python cli.py "NLP" "大语言模型" --llm deepseek --api-key sk-xxx
    uv run python cli.py "CCF论文" --version 2
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.generator import CopyGenerator
from llm.base import DummyLLM


def main():
    parser = argparse.ArgumentParser(
        description="闲鱼学术辅导文案生成器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
        "  uv run python cli.py 目标检测 YOLO\n"
        "  uv run python cli.py NLP 大模型 --llm deepseek --api-key sk-xxx",
    )
    parser.add_argument("keywords", nargs="+", help="关键词，如：目标检测 YOLO CCF")
    parser.add_argument("--llm", default="", choices=["deepseek", "qwen", "openai"],
                        help="使用 LLM 润色")
    parser.add_argument("--api-key", default="", help="LLM API Key")
    parser.add_argument("--model", default="", help="模型名 (默认自动选)")
    parser.add_argument("--base-url", default="", help="API 地址 (默认自动选)")
    parser.add_argument("--output", "-o", default="", help="输出 JSON 文件路径")
    parser.add_argument("--no-llm", action="store_true", help="仅使用模板，不调用 LLM")

    args = parser.parse_args()

    # Build LLM client
    llm = DummyLLM()
    if args.llm and not args.no_llm:
        llm = _build_llm(args)

    # Generate
    gen = CopyGenerator(llm_client=llm)
    result = gen.generate(args.keywords, use_llm=bool(args.llm and not args.no_llm))

    # Output
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"已输出到 {args.output}")

    _print_result(result)


def _build_llm(args) -> DummyLLM:
    from llm.openai_compat import OpenAICompat

    configs = {
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "model": args.model or "deepseek-chat",
        },
        "qwen": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": args.model or "qwen-plus",
        },
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "model": args.model or "gpt-4o",
        },
    }

    cfg = configs.get(args.llm, configs["deepseek"])
    base_url = args.base_url or cfg["base_url"]
    model = args.model or cfg["model"]
    api_key = args.api_key or _env_key(args.llm)

    if not api_key:
        print(f"[警告] 未设置 {args.llm.upper()}_API_KEY，将使用纯模板模式")
        return DummyLLM()

    return OpenAICompat(api_key=api_key, base_url=base_url, model=model)


def _env_key(provider: str) -> str:
    import os
    mapping = {
        "deepseek": "DEEPSEEK_API_KEY",
        "qwen": "DASHSCOPE_API_KEY",
        "openai": "OPENAI_API_KEY",
    }
    return os.environ.get(mapping.get(provider, ""))


def _print_result(result: dict):
    keywords = "、".join(result["keywords"])
    check = result["violations_check"]

    print()
    print("=" * 60)
    print(f"  关键词: {keywords}")
    print(f"  安全检测: {'通过' if check['safe'] else '有违禁词!'}")
    if check["violations"]:
        print(f"  违禁词: {', '.join(check['violations'])}")
    print("=" * 60)

    for v in result["variants"]:
        print(f"\n--- {v['version']} ({v['style']}) ---")
        print(f"标题: {v['title']}")
        print(f"详情:")
        print(v["body"])

    print()
    print("=" * 60)
    print(f"共生成 {len(result['variants'])} 个版本")


if __name__ == "__main__":
    main()
