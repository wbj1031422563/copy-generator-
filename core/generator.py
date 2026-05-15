"""Copy generation engine — LLM-first with template fallback + anti-detection."""

from __future__ import annotations

import logging

from core.anti_detect import AntiDetect
from core.context import build_generation_context
from core.data_loader import load_profile, load_services, load_style
from core.llm_parse import parse_copy_response
from core.prompt_builder import (
    build_compliance_polish_prompt,
    build_refine_prompt,
    build_system_prompt,
    build_user_prompt,
)
from core.templates import build_body, build_tags, build_title

logger = logging.getLogger(__name__)

STYLE_LABELS = {
    "comprehensive": "标准版",
    "concise_casual": "简洁版",
    "case_led": "案例版",
}


class CopyGenerator:
    def __init__(self, llm_client=None):
        self.profile = load_profile()
        self.services = load_services()
        self.style = load_style()
        self.anti_detect = AntiDetect()
        self.llm = llm_client

    def generate(self, keywords: list[str], use_llm: bool = False) -> dict:
        """Generate complete copy for a given set of keywords."""
        version_count = self.style.get("version_count", 3)
        variants = []
        tags = build_tags(keywords, self.services)
        max_title = self.style.get("max_title_len", 30)
        max_body = self.style.get("max_body_len", 500)

        variant_items = list(self.style.get("variants", {}).items())[:version_count]

        for variant_name, variant_cfg in variant_items:
            variant_style = variant_cfg.get("style", "comprehensive")

            title, body, source = self._produce_variant(
                keywords, variant_style, use_llm=use_llm
            )

            title = self.anti_detect.sanitize(title)[:max_title]
            body = self.anti_detect.sanitize(body)[:max_body]

            if use_llm and self.llm:
                title, body = self._maybe_compliance_polish(
                    keywords, variant_style, title, body
                )
                title = self.anti_detect.sanitize(title)[:max_title]
                body = self.anti_detect.sanitize(body)[:max_body]

            variants.append({
                "version": variant_name,
                "title": title,
                "body": body,
                "style": variant_style,
                "tags": tags,
                "source": source,
            })

        all_text = " ".join(v["title"] + " " + v["body"] for v in variants)
        safe, violations = self.anti_detect.validate(all_text)

        return {
            "keywords": keywords,
            "tags": tags,
            "variants": variants,
            "violations_check": {"safe": safe, "violations": violations},
            "llm_used": bool(use_llm and self.llm),
        }

    def generate_with_llm(self, keywords: list[str]) -> dict:
        return self.generate(keywords, use_llm=True)

    def _produce_variant(
        self,
        keywords: list[str],
        variant_style: str,
        use_llm: bool = False,
    ) -> tuple[str, str, str]:
        """Return (title, body, source) where source is 'llm' | 'template' | 'llm+template'."""
        draft_title = build_title(keywords, self.services, self.profile, style=variant_style)
        draft_body = build_body(keywords, self.services, self.profile, style=variant_style)

        if use_llm and self.llm:
            title, body = self._llm_generate(keywords, variant_style, draft_title, draft_body)
            if title and body and len(body) >= 200:
                return title, body, "llm"
            if title or body:
                merged_title = title or draft_title
                merged_body = body if len(body) >= 150 else draft_body
                refined_title, refined_body = self._llm_refine(
                    keywords, merged_title, merged_body, variant_style
                )
                if refined_title and refined_body:
                    return refined_title, refined_body, "llm+template"
            logger.warning("LLM output weak for style=%s, using template", variant_style)

        return draft_title, draft_body, "template"

    def _llm_generate(
        self,
        keywords: list[str],
        variant_style: str,
        draft_title: str,
        draft_body: str,
    ) -> tuple[str, str]:
        if not self.llm:
            return "", ""

        ctx = build_generation_context(keywords, variant_style)
        system = build_system_prompt()
        user = build_user_prompt(ctx, draft_title, draft_body)

        try:
            response = self.llm.complete(
                user,
                system=system,
                temperature=0.62,
                max_tokens=1200,
            )
        except TypeError:
            response = self.llm.complete(user)
        except Exception as e:
            logger.warning("LLM generate failed: %s", e)
            return "", ""

        title, body = parse_copy_response(response or "")
        return title, body

    def _llm_refine(
        self,
        keywords: list[str],
        title: str,
        body: str,
        variant_style: str,
    ) -> tuple[str, str]:
        if not self.llm:
            return title, body

        ctx = build_generation_context(keywords, variant_style)
        hint = STYLE_LABELS.get(variant_style, variant_style)
        prompt = build_refine_prompt(keywords, title, body, variant_style, hint, ctx)
        system = build_system_prompt()

        try:
            response = self.llm.complete(
                prompt, system=system, temperature=0.55, max_tokens=1200
            )
        except TypeError:
            response = self.llm.complete(prompt)
        except Exception as e:
            logger.warning("LLM refine failed: %s", e)
            return title, body

        new_title, new_body = parse_copy_response(response or "")
        return new_title or title, new_body or body

    def _maybe_compliance_polish(
        self,
        keywords: list[str],
        variant_style: str,
        title: str,
        body: str,
    ) -> tuple[str, str]:
        """Second pass when hard violations or soft AI/platform risks remain."""
        combined = f"{title}\n{body}"
        safe, violations = self.anti_detect.validate(combined)
        soft = self.anti_detect.detect_soft_risks(combined)
        if safe and not soft:
            return title, body

        ctx = build_generation_context(keywords, variant_style)
        prompt = build_compliance_polish_prompt(
            title, body, ctx.get("must_avoid"), soft
        )
        try:
            response = self.llm.complete(
                prompt,
                system=build_system_prompt(),
                temperature=0.4,
                max_tokens=1200,
            )
        except TypeError:
            response = self.llm.complete(prompt)
        except Exception as e:
            logger.warning("Compliance polish failed: %s", e)
            return title, body

        new_title, new_body = parse_copy_response(response or "")
        if new_title and new_body:
            return new_title, new_body
        return title, body
