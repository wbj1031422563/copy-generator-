"""Storage layer: SQLite (default) or MySQL (optional).

Configure MySQL via `data/db_config.json` or environment variables:
  COPYGEN_DB_TYPE=mysql
  MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE

Quality loop: table `good_copies` stores user-favorited listings for few-shot prompts.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

DATA_DIR = Path(__file__).parent.parent / "data"
DB_PATH = DATA_DIR / "history.db"
DB_CONFIG_PATH = DATA_DIR / "db_config.json"


def _load_db_config() -> dict:
    cfg: dict[str, Any] = {"type": "sqlite"}
    if DB_CONFIG_PATH.exists():
        try:
            file_cfg = json.loads(DB_CONFIG_PATH.read_text(encoding="utf-8"))
            if isinstance(file_cfg, dict):
                cfg.update(file_cfg)
        except (json.JSONDecodeError, OSError):
            pass

    db_type = os.environ.get("COPYGEN_DB_TYPE", cfg.get("type", "sqlite")).lower()
    cfg["type"] = db_type

    if db_type == "mysql":
        cfg.setdefault("host", os.environ.get("MYSQL_HOST", "127.0.0.1"))
        cfg.setdefault("port", int(os.environ.get("MYSQL_PORT", cfg.get("port", 3306))))
        cfg.setdefault("user", os.environ.get("MYSQL_USER", "root"))
        cfg.setdefault("password", os.environ.get("MYSQL_PASSWORD", cfg.get("password", "")))
        cfg.setdefault("database", os.environ.get("MYSQL_DATABASE", cfg.get("database", "copy_generator")))
    else:
        cfg["path"] = str(DB_PATH)

    return cfg


_CONFIG = _load_db_config()


def db_info() -> dict:
    """Public summary for API / diagnostics."""
    t = _CONFIG.get("type", "sqlite")
    info = {"type": t, "driver_ok": True}
    if t == "mysql":
        info.update({
            "host": _CONFIG.get("host"),
            "port": _CONFIG.get("port"),
            "database": _CONFIG.get("database"),
            "user": _CONFIG.get("user"),
        })
        try:
            import pymysql  # noqa: F401
        except ImportError:
            info["driver_ok"] = False
            info["error"] = "请安装 MySQL 驱动: uv sync --extra mysql"
    else:
        info["path"] = str(DB_PATH)
    return info


def is_mysql() -> bool:
    return _CONFIG.get("type") == "mysql"


def _placeholder() -> str:
    return "%s" if is_mysql() else "?"


def _adapt_sql(sql: str) -> str:
    if is_mysql():
        return sql.replace("?", "%s")
    return sql


class _Cursor:
    def __init__(self, cur, dialect: str):
        self._cur = cur
        self._dialect = dialect

    @property
    def lastrowid(self) -> int:
        return int(self._cur.lastrowid or 0)

    def fetchone(self) -> dict | None:
        row = self._cur.fetchone()
        if row is None:
            return None
        if isinstance(row, dict):
            return row
        if self._dialect == "sqlite":
            return dict(row)
        return dict(row)

    def fetchall(self) -> list[dict]:
        rows = self._cur.fetchall()
        if not rows:
            return []
        if isinstance(rows[0], dict):
            return list(rows)
        if self._dialect == "sqlite":
            return [dict(r) for r in rows]
        return [dict(r) for r in rows]


class _Connection:
    def __init__(self, raw, dialect: str):
        self._raw = raw
        self._dialect = dialect

    def execute(self, sql: str, params: tuple | list = ()) -> _Cursor:
        cur = self._raw.cursor()
        cur.execute(_adapt_sql(sql), tuple(params))
        return _Cursor(cur, self._dialect)

    def commit(self) -> None:
        self._raw.commit()

    def close(self) -> None:
        self._raw.close()


@contextmanager
def connect() -> Iterator[_Connection]:
    dialect = _CONFIG.get("type", "sqlite")
    if dialect == "mysql":
        try:
            import pymysql
            from pymysql.cursors import DictCursor
        except ImportError as e:
            raise RuntimeError(
                "MySQL 已配置但未安装 pymysql，请执行: uv sync --extra mysql"
            ) from e
        raw = pymysql.connect(
            host=_CONFIG["host"],
            port=int(_CONFIG["port"]),
            user=_CONFIG["user"],
            password=_CONFIG.get("password", ""),
            database=_CONFIG["database"],
            charset="utf8mb4",
            cursorclass=DictCursor,
            autocommit=False,
        )
    else:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        raw = sqlite3.connect(str(DB_PATH))
        raw.row_factory = sqlite3.Row

    conn = _Connection(raw, dialect)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn._raw.rollback()
        raise
    finally:
        conn.close()


def init_schema() -> None:
    """Create tables on SQLite or MySQL."""
    ph = _placeholder()
    if is_mysql():
        history_ddl = f"""
        CREATE TABLE IF NOT EXISTS history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            keywords TEXT NOT NULL,
            style VARCHAR(64),
            variants LONGTEXT NOT NULL,
            meta LONGTEXT NOT NULL,
            created_at VARCHAR(64) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        templates_ddl = f"""
        CREATE TABLE IF NOT EXISTS templates (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL UNIQUE,
            content LONGTEXT NOT NULL,
            updated_at VARCHAR(64) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
        good_ddl = f"""
        CREATE TABLE IF NOT EXISTS good_copies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            keywords TEXT NOT NULL,
            title VARCHAR(255) NOT NULL,
            body LONGTEXT NOT NULL,
            style VARCHAR(64),
            note VARCHAR(512) DEFAULT '',
            created_at VARCHAR(64) NOT NULL
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        """
    else:
        history_ddl = """
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keywords TEXT NOT NULL,
            style TEXT,
            variants TEXT NOT NULL,
            meta TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL
        )
        """
        templates_ddl = """
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            content TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
        good_ddl = """
        CREATE TABLE IF NOT EXISTS good_copies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keywords TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            style TEXT,
            note TEXT DEFAULT '',
            created_at TEXT NOT NULL
        )
        """

    with connect() as db:
        db.execute(history_ddl)
        db.execute(templates_ddl)
        db.execute(good_ddl)
        _migrate_history_meta(db)


def _migrate_history_meta(db: _Connection) -> None:
    if is_mysql():
        rows = db.execute(
            "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'history'"
        ).fetchall()
        cols = {r.get("COLUMN_NAME") or r.get("column_name") for r in rows}
        if "meta" not in cols:
            db.execute("ALTER TABLE history ADD COLUMN meta LONGTEXT NOT NULL")
    else:
        rows = db.execute("PRAGMA table_info(history)").fetchall()
        cols = {_row_column_name(r) for r in rows}
        if "meta" not in cols:
            db.execute("ALTER TABLE history ADD COLUMN meta TEXT NOT NULL DEFAULT '{}'")


def _row_column_name(row: dict) -> str:
    if isinstance(row, dict):
        return row.get("name") or row.get("NAME") or ""
    return str(row[1]) if len(row) > 1 else ""


def is_integrity_error(exc: BaseException) -> bool:
    if isinstance(exc, sqlite3.IntegrityError):
        return True
    try:
        import pymysql

        return isinstance(exc, pymysql.err.IntegrityError)
    except ImportError:
        return False


# ── Good copies (quality few-shot) ─────────────────────────


def add_good_copy(
    keywords: list[str],
    title: str,
    body: str,
    style: str = "",
    note: str = "",
) -> int:
    now = datetime.now(timezone.utc).isoformat()
    ph = _placeholder()
    with connect() as db:
        cur = db.execute(
            f"INSERT INTO good_copies (keywords, title, body, style, note, created_at) "
            f"VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph})",
            (
                json.dumps(keywords, ensure_ascii=False),
                title[:255],
                body,
                style,
                note,
                now,
            ),
        )
        return cur.lastrowid


def list_good_copies(limit: int = 20) -> list[dict]:
    ph = _placeholder()
    with connect() as db:
        rows = db.execute(
            f"SELECT * FROM good_copies ORDER BY id DESC LIMIT {ph}",
            (limit,),
        ).fetchall()
    out = []
    for r in rows:
        out.append({
            "id": r["id"],
            "keywords": json.loads(r["keywords"]),
            "title": r["title"],
            "body": r["body"],
            "style": r.get("style") or "",
            "note": r.get("note") or "",
            "created_at": r["created_at"],
        })
    return out


def delete_good_copy(copy_id: int) -> bool:
    ph = _placeholder()
    with connect() as db:
        cur = db.execute(f"DELETE FROM good_copies WHERE id = {ph}", (copy_id,))
        return cur._cur.rowcount > 0


def load_good_examples_for_prompt(limit: int = 3, max_chars: int = 1500) -> str:
    """Format favorited copies as prompt few-shot reference."""
    try:
        init_schema()
        copies = list_good_copies(limit=limit)
    except Exception:
        return ""
    if not copies:
        return ""
    parts = ["【你过去认可的优质文案参考，学习结构与语气，勿照抄】"]
    total = 0
    for c in copies:
        block = f"标题：{c['title']}\n详情：{c['body'][:400]}"
        if total + len(block) > max_chars:
            break
        parts.append(block)
        total += len(block)
    return "\n\n".join(parts)
