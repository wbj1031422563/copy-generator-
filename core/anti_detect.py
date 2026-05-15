"""Anti-detection: sensitive word replacement and variant generation.

Three layers of protection:
1. Direct replacement — exact match of risky words → safe alternatives
2. Context replacement — phrases that contain risky patterns → rewritten versions
3. Must-avoid check — final validation that no banned words remain
"""

import re
from core.data_loader import load_sensitive_words


class AntiDetect:
    def __init__(self):
        rules = load_sensitive_words()
        self.direct_replace = rules.get("direct_replace", {})
        self.context_replace = rules.get("context_replace", {})
        self.phrase_replace = rules.get("phrase_replace", {})
        self.must_avoid = rules.get("must_avoid", [])
        self.safe_phrases = rules.get("safe_phrases", [])
        self.ai_avoid_phrases = rules.get("ai_avoid_phrases", [])
        self.ai_soft_detect = rules.get("ai_soft_detect", self.ai_avoid_phrases)
        self.platform_avoid = rules.get("platform_avoid", [])

    def sanitize(self, text: str) -> str:
        """Apply all sanitization layers to a text.

        Safe phrases (like "诚信第一") are protected before replacement
        to avoid false positives.
        """
        # Protect safe phrases with placeholders
        placeholders = {}
        for i, phrase in enumerate(self.safe_phrases):
            if phrase in text:
                placeholder = f"__SAFE_{i}__"
                placeholders[placeholder] = phrase
                text = text.replace(phrase, placeholder)

        text = self._apply_direct_replace(text)
        text = self._apply_context_replace(text)
        text = self._apply_phrase_replace(text)

        # Restore safe phrases
        for placeholder, original in placeholders.items():
            text = text.replace(placeholder, original)

        return text

    def validate(self, text: str) -> tuple[bool, list[str]]:
        """Check if text contains any must-avoid words. Returns (is_safe, violations)."""
        violations = []
        lower = text.lower()
        for word in self.must_avoid:
            if word.lower() in lower:
                violations.append(word)
        return len(violations) == 0, violations

    def detect_soft_risks(self, text: str) -> list[str]:
        """AI-typical or platform-risky phrases (for polish pass, not hard fail)."""
        hits: list[str] = []
        for phrase in self.ai_soft_detect + self.platform_avoid:
            if phrase and phrase in text:
                hits.append(phrase)
        return hits

    def _apply_direct_replace(self, text: str) -> str:
        for risky, safe in self.direct_replace.items():
            if risky in text:
                text = text.replace(risky, safe)
        return text

    def _apply_context_replace(self, text: str) -> str:
        for risky, safe in self.context_replace.items():
            if risky in text:
                text = text.replace(risky, safe)
        return text

    def _apply_phrase_replace(self, text: str) -> str:
        for risky, safe in self.phrase_replace.items():
            if risky in text:
                text = text.replace(risky, safe)
        return text

    def generate_variants(self, title: str, body: str, count: int = 3) -> list[dict]:
        """Generate multiple semantically-equivalent variants.

        Variant strategies:
        - v1: original (sanitized)
        - v2: reorder sections (services-first → identity-first)
        - v3: simplified (shorter sentences, fewer technical details)
        """
        variants = [{"title": title, "body": body}]

        if count >= 2:
            v2_title = self._shuffle_title(title)
            v2_body = self._reorder_sections(body)
            variants.append({"title": v2_title, "body": v2_body})

        if count >= 3:
            v3_title = self._simplify_title(title)
            v3_body = self._simplify_body(body)
            variants.append({"title": v3_title, "body": v3_body})

        return variants[:count]

    def _shuffle_title(self, title: str) -> str:
        """Swap keyword order or restructure the title."""
        # Move keyword to front if it's not already
        parts = title.split(" ")
        if len(parts) >= 3:
            # Swap first and second segments
            parts[0], parts[1] = parts[1], parts[0]
            return " ".join(parts)
        return title

    def _reorder_sections(self, body: str) -> str:
        """Reorder body sections: identity-first → services-first."""
        lines = body.strip().split("\n")
        if len(lines) >= 6:
            # Swap first third with second third
            n = len(lines) // 3
            a = lines[:n]
            b = lines[n : 2 * n]
            c = lines[2 * n :]
            return "\n".join(b + a + c)
        return body

    def _simplify_title(self, title: str) -> str:
        """Shorten title by ~30%."""
        if len(title) > 20:
            return title[: int(len(title) * 0.7)].rstrip("，。 ")
        return title

    def _simplify_body(self, body: str) -> str:
        """Shorten body by keeping only key sections."""
        lines = body.strip().split("\n")
        if len(lines) > 8:
            # Keep first half
            return "\n".join(lines[: len(lines) // 2])
        return body
