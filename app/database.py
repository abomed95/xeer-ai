"""Accès base de données : PostgreSQL en production, SQLite en local.

Quand `DATABASE_URL` est défini (base managée DigitalOcean, Heroku…), les
données sont stockées dans PostgreSQL et **survivent aux redéploiements**.
Sinon, on retombe sur un fichier SQLite, pratique en développement.

Une fine couche de compatibilité (`_translate`) permet à tout le code métier de
rester écrit en SQL « SQLite » (placeholders `?`, `INSERT OR IGNORE`,
`cursor.lastrowid`) tout en s'exécutant tel quel sur PostgreSQL.
"""
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from app import config

# PostgreSQL dès qu'une URL de connexion est fournie.
IS_POSTGRES = config.DATABASE_URL.startswith(("postgres://", "postgresql://"))

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


# --------------------------------------------------------------------------
# Compatibilité PostgreSQL
# --------------------------------------------------------------------------

_INSERT_RE = re.compile(r"^\s*INSERT\s", re.IGNORECASE)
_INSERT_OR_IGNORE_RE = re.compile(r"INSERT\s+OR\s+IGNORE\s+INTO", re.IGNORECASE)


def _pg_schema(schema: str) -> str:
    """Traduit le schéma SQLite en schéma PostgreSQL équivalent."""
    return schema.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")


def _translate(sql: str) -> tuple[str, bool]:
    """Adapte une requête SQLite à PostgreSQL.

    Renvoie `(sql_traduit, returning_id)` où `returning_id` indique qu'un
    `RETURNING id` a été ajouté pour émuler `cursor.lastrowid`.
    """
    ignore_conflict = bool(_INSERT_OR_IGNORE_RE.search(sql))
    if ignore_conflict:
        sql = _INSERT_OR_IGNORE_RE.sub("INSERT INTO", sql)

    sql = sql.replace("?", "%s")

    returning = False
    if _INSERT_RE.match(sql):
        if ignore_conflict:
            sql += " ON CONFLICT DO NOTHING"
        if "RETURNING" not in sql.upper():
            sql += " RETURNING id"
            returning = True
    return sql, returning


class _PgCursor:
    """Expose l'interface d'un curseur sqlite3 (fetchone/fetchall/lastrowid)."""

    def __init__(self, cursor, pending_row=None, lastrowid=None):
        self._cursor = cursor
        self._pending_row = pending_row
        self._pending_consumed = False
        self.lastrowid = lastrowid

    def fetchone(self):
        # Une ligne déjà lue via RETURNING est restituée une seule fois.
        if self._pending_row is not None and not self._pending_consumed:
            self._pending_consumed = True
            return self._pending_row
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount


class _PgConnection:
    """Expose l'interface d'une connexion sqlite3, traduction SQL incluse."""

    def __init__(self, connection):
        self._connection = connection

    def execute(self, sql: str, params=()):
        translated, returning = _translate(sql)
        cursor = self._connection.cursor()
        cursor.execute(translated, params)

        pending_row = None
        lastrowid = None
        if returning:
            pending_row = cursor.fetchone()
            if pending_row is not None:
                lastrowid = pending_row.get("id")
        return _PgCursor(cursor, pending_row, lastrowid)

    def executescript(self, script: str):
        self._connection.cursor().execute(_pg_schema(script))


@contextmanager
def get_db():
    if IS_POSTGRES:
        import psycopg
        from psycopg.rows import dict_row

        conn = psycopg.connect(config.DATABASE_URL, row_factory=dict_row)
        try:
            yield _PgConnection(conn)
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(config.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def init_db():
    with get_db() as db:
        db.executescript(SCHEMA)


def backend_name() -> str:
    """Nom du moteur utilisé — exposé par /api/health pour le diagnostic."""
    return "postgresql" if IS_POSTGRES else "sqlite"


def row_to_dict(row) -> dict | None:
    return dict(row) if row is not None else None
