"""Paiement par carte Visa / MasterCard via une passerelle compatible Stripe.

En mode sandbox (défaut), le paiement est simulé. En mode live, renseigner
CARD_GATEWAY_SECRET_KEY (et CARD_GATEWAY_API_URL si différent de Stripe).
"""
import uuid

from app import config


def initiate(payment: dict, *, method: str = "card", **_) -> dict:
    if config.PAYMENTS_MODE != "live":
        return {
            "status": "pending",
            "provider_reference": f"CARD-SANDBOX-{uuid.uuid4().hex[:10].upper()}",
            "instructions": (
                f"[SANDBOX] Paiement {method.upper()} de "
                f"{payment['amount_usd']:.2f} USD prêt à être confirmé."
            ),
        }

    import requests

    if not config.CARD_GATEWAY_SECRET_KEY:
        raise RuntimeError("CARD_GATEWAY_SECRET_KEY manquant pour les paiements carte.")

    resp = requests.post(
        f"{config.CARD_GATEWAY_API_URL.rstrip('/')}/payment_intents",
        auth=(config.CARD_GATEWAY_SECRET_KEY, ""),
        data={
            "amount": int(round(payment["amount_usd"] * 100)),
            "currency": "usd",
            "description": f"Xeer AI — abonnement {payment['plan']}",
            "metadata[reference]": payment["reference"],
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "status": "pending",
        "provider_reference": str(data.get("id", "")),
        "instructions": "Confirmez le paiement avec votre carte.",
        "client_secret": data.get("client_secret"),
    }
