"""Modular prompt skills for stable, Xianyu-safe, human-like copy.

Synthesized from:
- REQUIREMENTS.md (compliance & structure)
- humanizer skill (anti-AI patterns, natural voice)
- sensitive_words.json (platform risk lexicon)
"""

from __future__ import annotations

from core.data_loader import load_sensitive_words


def skill_xianyu_compliance(must_avoid: list[str] | None = None) -> str:
    """Skill 1: Platform compliance — hard constraints."""
    rules = load_sensitive_words()
    banned = must_avoid or rules.get("must_avoid", [])
    banned_line = "、".join(banned[:20]) if banned else "代写、枪手、包过、保过、包录用等"

    safe_examples = "、".join(rules.get("safe_phrases", [])[:8])

    return f"""【技能·闲鱼合规】硬性规则（违反即废稿）
1. 绝对禁止词（正文与标题均不可出现，含谐音变体）：{banned_line}
2. 禁止：标价/优惠/付款/下单/拍下、论文买卖、承诺必过/包录用/保过、枪手、代写、代做毕设
3. 禁止：全网第一/销量第一/国家级认证等夸大背书；禁止外链、二维码、微信号/VX
4. 允许且推荐的安全表述：{safe_examples}（用于建立信任，但不要堆砌）
5. 服务表述用：提供思路、打磨 idea、写作指导、协助投稿、会议讲解、环境配置（勿用「代」字组合）"""


def skill_anti_ai_humanizer() -> str:
    """Skill 2: De-AI / human voice (condensed from humanizer skill)."""
    rules = load_sensitive_words()
    ai_phrases = "、".join(rules.get("ai_avoid_phrases", [])[:25])

    return f"""【技能·去 AI 腔】写成真人博士闲鱼帖，而非 ChatGPT 广告
- 禁止套话：{ai_phrases}
- 禁止：综上所述/值得一提的是/不仅…而且…/首先其次最后（机械结构）
- 禁止：过度排比、每条相同句式、空洞形容词（优质/专业/极致/全方位/一站式/赋能/助力/深耕）
- 要做：句长有短有长；可第一人称「我」；技术词具体（算法/会议/任务名）；偶尔口语（欢迎私聊、有问题先约会议）
- 不做：机构口吻（我们团队/公司/机构）、客服模板（亲/宝贝/不满意退款）
- 标点：少用破折号——堆砌；少用 emoji；不要 Markdown 小标题
- 输出前自检：「这段话像不像闲鱼上真人写的辅导帖？」不像则改"""


def skill_listing_structure(variant_style: str) -> str:
    """Skill 3: Stable listing structure for Xianyu."""
    if variant_style == "concise_casual":
        body_guide = "2-3 段：身份+方向 → 能帮什么 → 私聊/会议"
        length = "250-380 字"
    elif variant_style == "case_led":
        body_guide = "开头 1 段具体成果/交叉案例 → 方向与会议 → 服务 → 适合谁 → 引导私聊"
        length = "300-480 字"
    else:
        body_guide = "身份 → 主攻方向与技术点 → 会议/分区层次 → 服务内容（自然融入，非机械列表）→ 适合人群 → 私聊/腾讯会议"
        length = "300-500 字"

    return f"""【技能·闲鱼结构】稳定骨架（{variant_style}）
- 标题：≤30 字，核心关键词靠前，不加标点符号堆砌
- 详情：{length}，{body_guide}
- 关键词自然出现 2-4 次，同词不要连续重复
- 结尾统一轻引导：私聊/预约腾讯会议预沟通（不写价格）"""


def skill_self_check(must_avoid: list[str] | None = None) -> str:
    """Skill 4: Pre-output checklist for model."""
    banned = "、".join((must_avoid or [])[:12])
    return f"""【技能·输出前自检】生成 TITLE/BODY 前在脑中逐项确认：
□ 无禁止词：{banned}
□ 无价格、无「包过/保过/代写」类承诺
□ 不像 AI 广告：无套话、无机械「首先其次」
□ 像个人博士：有具体技术/会议名，语气真诚克制
□ 字数与格式符合要求
全部通过后再输出，仅输出两行：TITLE: … 与 BODY: …（正文可换行，不要代码块）"""


def skill_stable_output_format() -> str:
    return """【技能·稳定格式】
TITLE: <一行标题，无引号>
BODY: <详情正文，可多段，段间空行>
（不要输出其他任何解释、前言、后记）"""


def build_compliance_polish_prompt(
    title: str,
    body: str,
    must_avoid: list[str] | None = None,
    soft_hits: list[str] | None = None,
) -> str:
    """Short second-pass prompt: fix compliance + AI tone only."""
    banned = "、".join((must_avoid or [])[:15])
    soft = "、".join(soft_hits or []) or "无"

    return f"""你是闲鱼文案合规编辑。只做最小改动：去掉违规与 AI 套话，保持原意、人设与技术细节。

禁止词（必须清除或改写）：{banned}
需弱化的 AI/营销套话：{soft}

原文：
TITLE: {title}
BODY:
{body}

要求：标题≤30字；保留博士个人辅导身份；不写价格；输出格式：
TITLE: …
BODY: …"""


def assemble_generation_skills(ctx: dict) -> str:
    """Combine all skills for the user prompt."""
    style = ctx.get("variant_style", "comprehensive")
    parts = [
        skill_xianyu_compliance(ctx.get("must_avoid")),
        skill_anti_ai_humanizer(),
        skill_listing_structure(style),
        skill_self_check(ctx.get("must_avoid")),
        skill_stable_output_format(),
    ]
    return "\n\n".join(parts)
