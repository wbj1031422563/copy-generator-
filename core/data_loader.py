"""Load and manage user data files (profile, services, style, sensitive words)."""

import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"


def load_profile() -> dict:
    return _load_json("profile.json")


def load_services() -> dict:
    return _load_json("services.json")


def load_style() -> dict:
    return _load_json("style.json")


def load_sensitive_words() -> dict:
    return _load_json("sensitive_words.json")


def load_copy_examples(max_chars: int = 2000) -> str:
    """Load style reference excerpts for LLM prompts."""
    path = DATA_DIR / "copy_examples.txt"
    if not path.exists():
        # Fallback: parent repo example file
        alt = DATA_DIR.parent.parent / "文案示例" / "文案示例.txt"
        if alt.exists():
            raw = alt.read_text(encoding="utf-8")
        else:
            return ""
    else:
        raw = path.read_text(encoding="utf-8")

    lines = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("["):
            continue
        if len(line) < 12:
            continue
        lines.append(line)

    text = "\n".join(lines)
    return text[:max_chars] if max_chars else text


def _load_json(filename: str) -> dict:
    path = DATA_DIR / filename
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}
