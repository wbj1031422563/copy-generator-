"""Parse LLM copy output into title + body."""

from __future__ import annotations

import json
import re


def parse_copy_response(text: str) -> tuple[str, str]:
    """Extract title and body from model output. Returns ('', '') if unparseable."""
    if not text or not text.strip():
        return "", ""

    text = text.strip()
    # Strip markdown code fences
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```\s*$", "", text).strip()

    # JSON object
    if text.startswith("{"):
        try:
            data = json.loads(text)
            title = (data.get("title") or data.get("标题") or "").strip()
            body = (data.get("body") or data.get("详情") or data.get("content") or "").strip()
            if title or body:
                return title, body
        except json.JSONDecodeError:
            pass

    title, body = _parse_labeled_blocks(text)
    if title or body:
        return title, body

    return "", ""


def _parse_labeled_blocks(text: str) -> tuple[str, str]:
    title = ""
    body = ""

    # TITLE: ... BODY: ... (body may be multiline)
    m = re.search(
        r"(?:TITLE|标题)\s*[:：]\s*(.+?)(?:\n\s*(?:BODY|详情|正文)\s*[:：]\s*)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        title = m.group(1).strip().strip("\"'")
        rest = text[m.end() :].strip()
        body = rest.strip("\"'")
        return _clean_title(title), _clean_body(body)

    lines = text.split("\n")
    body_lines: list[str] = []
    in_body = False
    for line in lines:
        stripped = line.strip()
        upper = stripped.upper()
        if re.match(r"^(TITLE|标题)\s*[:：]", stripped, re.IGNORECASE):
            title = re.split(r"[:：]", stripped, 1)[-1].strip().strip("\"'")
            in_body = False
            continue
        if re.match(r"^(BODY|详情|正文)\s*[:：]", stripped, re.IGNORECASE):
            part = re.split(r"[:：]", stripped, 1)[-1].strip()
            if part:
                body_lines.append(part)
            in_body = True
            continue
        if in_body:
            body_lines.append(line)
        elif not title and stripped and not stripped.startswith("#"):
            # First non-empty line as title fallback
            if len(stripped) <= 35:
                title = stripped.strip("\"'")

    if body_lines:
        body = "\n".join(body_lines).strip().strip("\"'")
    elif not body and title and len(text) > len(title) + 20:
        # Body is everything after first line
        idx = text.find(title) + len(title)
        body = text[idx:].strip().lstrip(":：-\n").strip()

    return _clean_title(title), _clean_body(body)


def _clean_title(title: str) -> str:
    title = re.sub(r"^#+\s*", "", title).strip()
    return title[:30]


def _clean_body(body: str) -> str:
    body = re.sub(r"^#+\s*", "", body, flags=re.MULTILINE).strip()
    return body[:500]
