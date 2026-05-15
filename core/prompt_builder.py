"""LLM prompts aligned with REQUIREMENTS.md + prompt_skills."""

from __future__ import annotations

from core.prompt_skills import (
    assemble_generation_skills,
    build_compliance_polish_prompt,
    skill_anti_ai_humanizer,
    skill_xianyu_compliance,
)


def build_system_prompt() -> str:
    return (
        "你是闲鱼学术辅导商品文案专家，写出「像真人博士发的帖」且能通过平台审核的文案。\n"
        "身份：个人博士个人承接（非中介、非机构）；语气专业真诚、技术细节具体。\n"
        "写作时同步执行：闲鱼合规、去 AI 腔、稳定 TITLE/BODY 格式三项技能。\n"
        "禁止输出 Markdown、解释、自检过程；只输出 TITLE: 与 BODY: 两行起头的成品。\n\n"
        + skill_xianyu_compliance()
        + "\n\n"
        + skill_anti_ai_humanizer()
    )


def build_user_prompt(ctx: dict, draft_title: str, draft_body: str) -> str:
    p = ctx["profile"]
    identity = p.get("identity", "")
    roles = "、".join(p.get("role_tags", []))
    audience = "、".join(p.get("audience", []))
    highlight = p.get("highlight", "")
    contact = p.get("contact", "")
    extra = p.get("extra", "")

    domains = "、".join(ctx["domains"][:6]) or "深度学习、计算机视觉"
    topics = "、".join(ctx["topic_keywords"][:12])
    cross = "、".join(ctx["cross_fields"]) if ctx["cross_fields"] else "无特别指定"
    confs = "、".join(ctx["conferences"][:8])
    levels = ctx["levels"]
    services = "\n".join(f"- {t}" for t in ctx["service_types"][:6])
    keywords = "、".join(ctx["keywords"])
    examples = ctx.get("examples_excerpt", "")
    style_hint = ctx.get("style_hint", "")
    skills_block = assemble_generation_skills(ctx)

    quality_note = ""
    if ctx.get("has_good_examples"):
        quality_note = (
            "## 优质范例（对齐节奏与密度，禁止照抄句子）\n"
            "用户已收藏认可范例，请模仿其「真人感」与段落节奏。\n"
        )

    return f"""请为闲鱼撰写一条学术辅导商品文案。

{skills_block}

---

## 人设素材
- 身份：{identity}；标签：{roles}
- 亮点：{highlight}
- 联系语气：{contact}
- 背景：{extra}
- 受众：{audience}

## 本次关键词
{keywords}

## 技术与服务（自然融入，禁止机械堆砌）
- 方向：{domains}
- 技术词：{topics}
- 交叉领域：{cross}
- 会议：{confs}
- 层次：{levels}
- 服务：
{services}

## 风格
{style_hint}

{quality_note}
## 文风参考
{examples or "（无则按技能要求写）"}

## 模板草稿（仅作素材，须大幅改写为人话）
标题：{draft_title}
详情：
{draft_body}

请严格按【技能·稳定格式】输出。"""


def build_refine_prompt(
    keywords: list[str],
    title: str,
    body: str,
    variant_style: str,
    style_label: str,
    ctx: dict | None = None,
) -> str:
    """Refine pass with full skill stack."""
    ctx = ctx or {}
    skills = assemble_generation_skills({**ctx, "variant_style": variant_style})
    return f"""请润色以下闲鱼学术辅导文案（{style_label}）。

{skills}

关键词：{', '.join(keywords)}

标题：{title}
详情：
{body}

输出格式：
TITLE: <标题>
BODY: <详情>"""


# Re-export for generator compliance pass
__all__ = [
    "build_system_prompt",
    "build_user_prompt",
    "build_refine_prompt",
    "build_compliance_polish_prompt",
]
