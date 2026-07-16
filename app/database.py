"""Accès SQLite : schéma, connexions et helpers."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from app import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'user',            -- user | admin
    plan TEXT NOT NULL DEFAULT 'free',            -- free | premium | organization
    plan_expires_at TEXT,                         -- ISO, NULL = sans expiration
    org_name TEXT,
    custom_quota INTEGER,                         -- quota négocié (organisations)
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS questions_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    question TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    provider TEXT NOT NULL,                       -- waafi | cacbank | card
    method TEXT NOT NULL DEFAULT '',              -- ex: visa, mastercard, waafi
    amount_usd REAL NOT NULL,
    plan TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',       -- pending | completed | failed
    reference TEXT NOT NULL UNIQUE,
    provider_reference TEXT,
    created_at TEXT NOT NULL,
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,                          -- UUID
    user_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL,                           -- user | assistant
    content TEXT NOT NULL,
    sources TEXT,                                 -- JSON des sources citées
    feedback INTEGER,                             -- 1 = 👍, -1 = 👎, NULL = aucun
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS org_leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL,
    organization TEXT NOT NULL,
    message TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'new',           -- new | contacted | closed
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_questions_user ON questions_log(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_user ON conversations(user_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id, id);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


@contextmanager
def get_db():
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as db:
        db.executescript(SCHEMA)


def row_to_dict(row: sqlite3.Row | None) -> dict | None:
    return dict(row) if row is not None else None
