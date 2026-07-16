"""Routes de facturation : plans, checkout, confirmation, offres organisation."""
import uuid
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException

from app import config
from app.database import get_db, utcnow
from app.deps import get_current_user
from app.schemas import CheckoutRequest, ConfirmPaymentRequest, OrgLeadRequest
from app.services.accounts import user_out
from app.services.payments import PROVIDER_INFO, get_provider

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/plans")
def list_plans():
    return {
        "plans": [
            {
                "id": "free",
                "name": "Gratuit",
                "price_usd": 0,
                "period": "pour toujours",
                "quota": config.PLANS["free"]["quota"],
                "features": [
                    f"{config.PLANS['free']['quota']} questions par mois",
                    "Réponses avec citations de pages",
                    "Somali · Français · English",
                ],
            },
            {
                "id": "premium",
                "name": "Premium",
                "price_usd": config.PREMIUM_PRICE_USD,
                "period": "par mois",
                "quota": None,
                "features": [
                    "Questions illimitées",
                    "Mémoire de conversation",
                    "Historique et sources détaillées",
                    "Support prioritaire",
                ],
            },
            {
                "id": "organization",
                "name": "Organisation",
                "price_usd": None,
                "period": "prix négociable",
                "quota": None,
                "features": [
                    "Tarif négocié selon vos besoins",
                    "Comptes multiples pour vos équipes",
                    "Quota personnalisé ou illimité",
                    "Accompagnement dédié",
                ],
            },
        ],
        "providers": PROVIDER_INFO,
    }


@router.post("/checkout")
def checkout(payload: CheckoutRequest, user: dict = Depends(get_current_user)):
    if payload.plan != "premium":
        raise HTTPException(
            status_code=400,
            detail="Seul le plan Premium est payable en ligne. Pour une offre "
                   "Organisation, contactez-nous via le formulaire dédié.",
        )
    try:
        provider = get_provider(payload.provider)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    reference = f"XEER-{uuid.uuid4().hex[:12].upper()}"
    payment = {
        "reference": reference,
        "amount_usd": config.PREMIUM_PRICE_USD,
        "plan": "premium",
        "created_at": utcnow(),
    }

    try:
        result = provider.initiate(payment, phone=payload.phone, method=payload.method)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    with get_db() as db:
        db.execute(
            "INSERT INTO payments (user_id, provider, method, amount_usd, plan, "
            "status, reference, provider_reference, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user["id"], payload.provider, payload.method,
                config.PREMIUM_PRICE_USD, "premium", result["status"],
                reference, result.get("provider_reference", ""), payment["created_at"],
            ),
        )

    if result["status"] == "completed":
        _activate_premium(user["id"], reference)

    return {
        "reference": reference,
        "status": result["status"],
        "amount_usd": config.PREMIUM_PRICE_USD,
        "instructions": result.get("instructions", ""),
        "client_secret": result.get("client_secret"),
        "sandbox": config.PAYMENTS_MODE != "live",
    }


def _activate_premium(user_id: int, reference: str):
    expires = (datetime.now(timezone.utc)
               + timedelta(days=config.SUBSCRIPTION_DAYS)).isoformat()
    with get_db() as db:
        db.execute(
            "UPDATE payments SET status = 'completed', completed_at = ? "
            "WHERE reference = ?",
            (utcnow(), reference),
        )
        db.execute(
            "UPDATE users SET plan = 'premium', plan_expires_at = ? WHERE id = ?",
            (expires, user_id),
        )


@router.post("/confirm")
def confirm_payment(payload: ConfirmPaymentRequest, user: dict = Depends(get_current_user)):
    """Confirme un paiement en attente (simulation en sandbox ; en live la
    confirmation vient du webhook du fournisseur)."""
    with get_db() as db:
        row = db.execute(
            "SELECT * FROM payments WHERE reference = ? AND user_id = ?",
            (payload.reference, user["id"]),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Paiement introuvable.")
    payment = dict(row)

    if payment["status"] == "completed":
        return {"reference": payment["reference"], "status": "completed"}

    if config.PAYMENTS_MODE == "live":
        raise HTTPException(
            status_code=409,
            detail="Paiement en attente de confirmation par le fournisseur.",
        )

    _activate_premium(user["id"], payment["reference"])
    with get_db() as db:
        fresh_user = dict(db.execute(
            "SELECT * FROM users WHERE id = ?", (user["id"],)
        ).fetchone())
    return {
        "reference": payment["reference"],
        "status": "completed",
        "user": user_out(fresh_user),
    }


@router.post("/webhook/{provider_id}")
def payment_webhook(provider_id: str, payload: dict):
    """Callback serveur-à-serveur des fournisseurs (mode live).

    Chaque fournisseur envoie sa référence de transaction ; le paiement
    correspondant est complété et l'abonnement activé.
    """
    reference = (payload.get("reference")
                 or payload.get("referenceId")
                 or payload.get("metadata", {}).get("reference"))
    if not reference:
        raise HTTPException(status_code=400, detail="Référence manquante.")

    with get_db() as db:
        row = db.execute(
            "SELECT * FROM payments WHERE reference = ? AND provider = ?",
            (reference, provider_id),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Paiement introuvable.")

    payment = dict(row)
    if payment["status"] != "completed":
        _activate_premium(payment["user_id"], reference)
    return {"ok": True}


@router.get("/history")
def payment_history(user: dict = Depends(get_current_user)):
    with get_db() as db:
        rows = db.execute(
            "SELECT reference, provider, method, amount_usd, plan, status, "
            "created_at, completed_at FROM payments WHERE user_id = ? "
            "ORDER BY created_at DESC",
            (user["id"],),
        ).fetchall()
    return {"payments": [dict(r) for r in rows]}


@router.post("/org-lead")
def create_org_lead(payload: OrgLeadRequest):
    """Demande de devis Organisation (prix négociable) — accessible sans compte."""
    with get_db() as db:
        db.execute(
            "INSERT INTO org_leads (name, email, organization, message, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (payload.name.strip(), payload.email.lower().strip(),
             payload.organization.strip(), payload.message.strip(), utcnow()),
        )
    return {
        "message": "Merci ! Notre équipe commerciale vous contactera sous 24 h "
                   "pour établir une offre sur mesure.",
    }
