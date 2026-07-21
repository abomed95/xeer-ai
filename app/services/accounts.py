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


def ensure_demo_user(user_id: int) -> dict:
    """Re-matérialise un utilisateur de démonstration dans la base locale.

    En mode démo, la base SQLite peut ne pas persister d'une requête à l'autre
    (plusieurs instances derrière un load-balancer, système de fichiers
    éphémère du PaaS…). Lorsqu'un jeton signé valide pointe vers un utilisateur
    absent de la base de l'instance courante, on recrée une ligne minimale avec
    le même identifiant : le parcours reste fonctionnel et les contraintes de
    clé étrangère (conversations, questions_log…) sont satisfaites.
    """
    with get_db() as db:
        db.execute(
            "INSERT OR IGNORE INTO users "
            "(id, email, password_hash, full_name, role, plan, created_at) "
            "VALUES (?, ?, '', ?, 'user', 'free', ?)",
            (user_id, f"demo-{user_id}@xeer.ai", "Utilisateur démo", utcnow()),
        )
        row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(row)


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
