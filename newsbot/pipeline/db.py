"""News History Database (SQLite)."""
import json
import sys
import sqlite3
from datetime import datetime, timezone

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS news_items (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE,
    title TEXT,
    summary TEXT,
    source TEXT,
    region TEXT,
    trust REAL,
    published_at TEXT,          -- article publication time (UTC ISO)
    first_seen TEXT,            -- when our crawler first saw it
    image_url TEXT,
    score REAL,
    score_detail TEXT,
    cluster_key TEXT,
    used_in_episode TEXT
);
CREATE TABLE IF NOT EXISTS episodes (
    id TEXT PRIMARY KEY,        -- e.g. 2026-11-21-1800-uz
    slot TEXT,
    region TEXT,
    title TEXT,
    topic_key TEXT,             -- normalized tokens for duplicate detection
    event_date TEXT,            -- date the event happened (not article date)
    viral_score REAL,
    status TEXT,                -- draft|voiced|rendered|qc_failed|approved|published|skipped|error
    created_at TEXT,
    rendered_at TEXT,
    published_at TEXT,
    video_path TEXT,
    ig_media_id TEXT,
    is_update_of TEXT,
    similarity REAL,
    sources TEXT,
    error TEXT
);
CREATE TABLE IF NOT EXISTS media_assets (
    id INTEGER PRIMARY KEY,
    episode_id TEXT,
    file TEXT,
    source_url TEXT,
    license TEXT,
    author TEXT,
    title TEXT,
    kind TEXT
);
CREATE TABLE IF NOT EXISTS analytics (
    episode_id TEXT,
    fetched_at TEXT,
    metrics TEXT
);
CREATE TABLE IF NOT EXISTS log (
    ts TEXT, level TEXT, episode_id TEXT, msg TEXT
);
"""


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA)
    return c


def log(level: str, msg: str, episode_id: str | None = None):
    with conn() as c:
        c.execute("INSERT INTO log VALUES (?,?,?,?)", (now_utc(), level, episode_id, msg))
    print(f"[{level}] {episode_id or '-'} {msg}", file=sys.stderr)


def upsert_episode(ep_id: str, **fields):
    with conn() as c:
        row = c.execute("SELECT id FROM episodes WHERE id=?", (ep_id,)).fetchone()
        if "sources" in fields and not isinstance(fields["sources"], str):
            fields["sources"] = json.dumps(fields["sources"], ensure_ascii=False)
        if row:
            if fields:
                sets = ", ".join(f"{k}=?" for k in fields)
                c.execute(f"UPDATE episodes SET {sets} WHERE id=?", (*fields.values(), ep_id))
        else:
            fields.setdefault("created_at", now_utc())
            cols = ", ".join(["id", *fields])
            qs = ", ".join("?" * (len(fields) + 1))
            c.execute(f"INSERT INTO episodes ({cols}) VALUES ({qs})", (ep_id, *fields.values()))
