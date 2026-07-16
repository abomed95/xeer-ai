"""Conversations et messages persistés en base de données."""
import json
from uuid import uuid4

from app.database import get_db, utcnow


def create_conversation(user_id: int, title: str) -> str:
    conv_id = str(uuid4())
    now = utcnow()
    with get_db() as db:
        db.execute(
            "INSERT INTO conversations (id, user_id, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (conv_id, user_id, title[:80], now, now),
        )
    return conv_id


def get_conversation(conv_id: str, user_id: int) -> dict | None:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM conversations WHERE id = ? AND user_id = ?",
            (conv_id, user_id),
        ).fetchone()
    return dict(row) if row else None


def list_conversations(user_id: int, limit: int = 50) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT c.id, c.title, c.created_at, c.updated_at, "
            "(SELECT COUNT(*) FROM messages m WHERE m.conversation_id = c.id) AS message_count "
            "FROM conversations c WHERE c.user_id = ? "
            "ORDER BY c.updated_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def delete_conversation(conv_id: str, user_id: int) -> bool:
    with get_db() as db:
        cursor = db.execute(
            "DELETE FROM conversations WHERE id = ? AND user_id = ?",
            (conv_id, user_id),
        )
    return cursor.rowcount > 0


def get_messages(conv_id: str) -> list[dict]:
    with get_db() as db:
        rows = db.execute(
            "SELECT id, role, content, sources, feedback, created_at "
            "FROM messages WHERE conversation_id = ? ORDER BY id",
            (conv_id,),
        ).fetchall()
    messages = []
    for r in rows:
        msg = dict(r)
        msg["sources"] = json.loads(msg["sources"]) if msg["sources"] else []
        messages.append(msg)
    return messages


def add_message(conv_id: str, role: str, content: str, sources: list | None = None) -> int:
    now = utcnow()
    with get_db() as db:
        cursor = db.execute(
            "INSERT INTO messages (conversation_id, role, content, sources, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (conv_id, role, content,
             json.dumps(sources, ensure_ascii=False) if sources else None, now),
        )
        db.execute(
            "UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conv_id)
        )
    return cursor.lastrowid


def history_for_llm(conv_id: str, max_messages: int = 6) -> list[dict]:
    """Derniers messages au format OpenAI (role/content)."""
    messages = get_messages(conv_id)[-max_messages:]
    return [{"role": m["role"], "content": m["content"]} for m in messages]


def set_feedback(message_id: int, user_id: int, rating: int) -> bool:
    """Enregistre 👍 (1) / 👎 (-1) sur un message assistant de l'utilisateur."""
    with get_db() as db:
        cursor = db.execute(
            "UPDATE messages SET feedback = ? WHERE id = ? AND role = 'assistant' "
            "AND conversation_id IN (SELECT id FROM conversations WHERE user_id = ?)",
            (rating, message_id, user_id),
        )
    return cursor.rowcount > 0
