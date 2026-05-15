"""Database layer tests (SQLite)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.database import (
    add_good_copy,
    connect,
    db_info,
    delete_good_copy,
    init_schema,
    list_good_copies,
    load_good_examples_for_prompt,
)


def test_sqlite_info():
    info = db_info()
    assert info["type"] == "sqlite"


def test_good_copy_roundtrip():
    init_schema()
    cid = add_good_copy(
        ["YOLO", "检测"],
        "YOLO目标检测 博士辅导",
        "本人博士，主攻目标检测与YOLO系列算法改进。" * 8,
        style="comprehensive",
    )
    assert cid > 0
    items = list_good_copies(limit=5)
    assert any(i["id"] == cid for i in items)
    excerpt = load_good_examples_for_prompt(limit=2)
    assert "YOLO" in excerpt
    assert delete_good_copy(cid)


def test_history_insert():
    init_schema()
    with connect() as db:
        cur = db.execute(
            "INSERT INTO history (keywords, style, variants, meta, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ('["test"]', "all", "[]", "{}", "2026-01-01T00:00:00Z"),
        )
        assert cur.lastrowid > 0
