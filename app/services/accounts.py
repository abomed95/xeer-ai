"""Logique métier des comptes : plans, quotas, usage."""
from datetime import datetime, timezone

from app import config
from app.database import get_db, utcnow


def get_user_by_id(user_id: int) -> dict | None:
    with get_db() as db:
        row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row) if row else None


def get_user_by_email(email: str) -> dict | None:
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
        ).fetchone()
    return dict(row) if row else None


def effective_plan(user: dict) -> str:
    """Plan réel de l'utilisateur : retombe sur 'free' si l'abonnement a expiré."""
    plan = user["plan"]
    if plan == "free":
        return "free"
    expires = user.get("plan_expires_at")
    if expires:
        try:
            if datetime.fromisoformat(expires) < datetime.now(timezone.utc):
                return "free"
        except ValueError:
            pass
    return plan


def quota_for(user: dict) -> int | None:
    """Quota mensuel de questions (None = illimité)."""
    plan = effective_plan(user)
    if plan == "organization" and user.get("custom_quota"):
        return user["custom_quota"]
    return config.PLANS[plan]["quota"]


def questions_used_this_month(user_id: int) -> int:
    month_prefix = datetime.now(timezone.utc).strftime("%Y-%m")
    with get_db() as db:
        row = db.execute(
            "SELECT COUNT(*) AS n FROM questions_log "
            "WHERE user_id = ? AND created_at LIKE ?",
            (user_id, f"{month_prefix}%"),
        ).fetchone()
    return row["n"]


def log_question(user_id: int, question: str):
    with get_db() as db:
        db.execute(
            "INSERT INTO questions_log (user_id, question, created_at) VALUES (?, ?, ?)",
            (user_id, question[:500], utcnow()),
        )


def user_out(user: dict) -> dict:
    """Projection publique d'un utilisateur, avec quota et usage."""
    quota = quota_for(user)
    used = questions_used_this_month(user["id"])
    return {
        "id": user["id"],
        "email": user["email"],
        "full_name": user["full_name"],
        "role": user["role"],
        "plan": effective_plan(user),
        "plan_expires_at": user.get("plan_expires_at"),
        "org_name": user.get("org_name"),
        "quota": quota,
        "questions_used": used,
        "questions_remaining": None if quota is None else max(0, quota - used),
    }
