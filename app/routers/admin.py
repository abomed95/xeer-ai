"""Routes d'administration : statistiques, utilisateurs, paiements, leads."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from app import config
from app.database import get_db, utcnow
from app.deps import require_admin
from app.schemas import LeadStatusRequest, SetPlanRequest
from app.services.accounts import user_out

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/stats")
def stats(admin: dict = Depends(require_admin)):
    now = datetime.now(timezone.utc)
    month_prefix = now.strftime("%Y-%m")

    with get_db() as db:
        total_users = db.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
        new_users_month = db.execute(
            "SELECT COUNT(*) AS n FROM users WHERE created_at LIKE ?",
            (f"{month_prefix}%",),
        ).fetchone()["n"]
        premium_active = db.execute(
            "SELECT COUNT(*) AS n FROM users WHERE plan = 'premium' "
            "AND role != 'admin' "
            "AND (plan_expires_at IS NULL OR plan_expires_at > ?)",
            (now.isoformat(),),
        ).fetchone()["n"]
        org_active = db.execute(
            "SELECT COUNT(*) AS n FROM users WHERE plan = 'organization' "
            "AND (plan_expires_at IS NULL OR plan_expires_at > ?)",
            (now.isoformat(),),
        ).fetchone()["n"]
        questions_month = db.execute(
            "SELECT COUNT(*) AS n FROM questions_log WHERE created_at LIKE ?",
            (f"{month_prefix}%",),
        ).fetchone()["n"]
        questions_total = db.execute(
            "SELECT COUNT(*) AS n FROM questions_log"
        ).fetchone()["n"]
        revenue_month = db.execute(
            "SELECT COALESCE(SUM(amount_usd), 0) AS s FROM payments "
            "WHERE status = 'completed' AND completed_at LIKE ?",
            (f"{month_prefix}%",),
        ).fetchone()["s"]
        revenue_total = db.execute(
            "SELECT COALESCE(SUM(amount_usd), 0) AS s FROM payments "
            "WHERE status = 'completed'"
        ).fetchone()["s"]
        payments_by_provider = [
            dict(r) for r in db.execute(
                "SELECT provider, COUNT(*) AS count, "
                "COALESCE(SUM(amount_usd), 0) AS total_usd "
                "FROM payments WHERE status = 'completed' GROUP BY provider"
            ).fetchall()
        ]
        new_leads = db.execute(
            "SELECT COUNT(*) AS n FROM org_leads WHERE status = 'new'"
        ).fetchone()["n"]
        feedback = db.execute(
            "SELECT COALESCE(SUM(CASE WHEN feedback = 1 THEN 1 ELSE 0 END), 0) AS up, "
            "COALESCE(SUM(CASE WHEN feedback = -1 THEN 1 ELSE 0 END), 0) AS down "
            "FROM messages WHERE feedback IS NOT NULL"
        ).fetchone()

        # Séries des 30 derniers jours (questions et revenus) pour les graphiques
        since = (now - timedelta(days=29)).strftime("%Y-%m-%d")
        questions_daily = [
            dict(r) for r in db.execute(
                "SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS count "
                "FROM questions_log WHERE substr(created_at, 1, 10) >= ? "
                "GROUP BY day ORDER BY day",
                (since,),
            ).fetchall()
        ]
        revenue_daily = [
            dict(r) for r in db.execute(
                "SELECT substr(completed_at, 1, 10) AS day, "
                "COALESCE(SUM(amount_usd), 0) AS total_usd "
                "FROM payments WHERE status = 'completed' "
                "AND substr(completed_at, 1, 10) >= ? GROUP BY day ORDER BY day",
                (since,),
            ).fetchall()
        ]

    return {
        "users": {
            "total": total_users,
            "new_this_month": new_users_month,
            "premium_active": premium_active,
            "organization_active": org_active,
        },
        "questions": {"this_month": questions_month, "total": questions_total},
        "feedback": {
            "up": feedback["up"],
            "down": feedback["down"],
            "satisfaction_pct": (
                round(100 * feedback["up"] / (feedback["up"] + feedback["down"]))
                if (feedback["up"] + feedback["down"]) else None
            ),
        },
        "revenue": {
            "this_month_usd": revenue_month,
            "total_usd": revenue_total,
            "mrr_usd": premium_active * config.PREMIUM_PRICE_USD,
            "by_provider": payments_by_provider,
        },
        "leads": {"new": new_leads},
        "series": {"questions_daily": questions_daily, "revenue_daily": revenue_daily},
    }


@router.get("/users")
def list_users(admin: dict = Depends(require_admin), q: str = "", limit: int = 100):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM users WHERE email LIKE ? OR full_name LIKE ? "
            "ORDER BY created_at DESC LIMIT ?",
            (f"%{q}%", f"%{q}%", min(limit, 500)),
        ).fetchall()
    return {"users": [user_out(dict(r)) for r in rows]}


@router.put("/users/{user_id}/plan")
def set_user_plan(
    user_id: int, payload: SetPlanRequest, admin: dict = Depends(require_admin)
):
    if payload.plan not in config.PLANS:
        raise HTTPException(status_code=400, detail="Plan inconnu.")

    expires = None
    if payload.plan != "free" and payload.days > 0:
        expires = (datetime.now(timezone.utc)
                   + timedelta(days=payload.days)).isoformat()

    with get_db() as db:
        cursor = db.execute(
            "UPDATE users SET plan = ?, plan_expires_at = ?, custom_quota = ?, "
            "org_name = COALESCE(?, org_name) WHERE id = ?",
            (payload.plan, expires, payload.custom_quota, payload.org_name, user_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Utilisateur introuvable.")
        user = dict(db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone())
    return {"user": user_out(user)}


@router.get("/payments")
def list_payments(admin: dict = Depends(require_admin), limit: int = 100):
    with get_db() as db:
        rows = db.execute(
            "SELECT p.*, u.email FROM payments p JOIN users u ON u.id = p.user_id "
            "ORDER BY p.created_at DESC LIMIT ?",
            (min(limit, 500),),
        ).fetchall()
    return {"payments": [dict(r) for r in rows]}


@router.get("/leads")
def list_leads(admin: dict = Depends(require_admin)):
    with get_db() as db:
        rows = db.execute(
            "SELECT * FROM org_leads ORDER BY created_at DESC LIMIT 200"
        ).fetchall()
    return {"leads": [dict(r) for r in rows]}


@router.put("/leads/{lead_id}/status")
def set_lead_status(
    lead_id: int, payload: LeadStatusRequest, admin: dict = Depends(require_admin)
):
    if payload.status not in ("new", "contacted", "closed"):
        raise HTTPException(status_code=400, detail="Statut invalide.")
    with get_db() as db:
        cursor = db.execute(
            "UPDATE org_leads SET status = ? WHERE id = ?",
            (payload.status, lead_id),
        )
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Demande introuvable.")
    return {"ok": True}
