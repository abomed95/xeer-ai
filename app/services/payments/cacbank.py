"""Intégration CAC Bank (CAC Pay).

En mode sandbox (défaut), le paiement est simulé. En mode live, renseigner
CACBANK_API_URL, CACBANK_MERCHANT_ID et CACBANK_API_KEY (fournis par la
banque lors de l'ouverture du compte marchand CAC Pay).
"""
import uuid

from app import config


def initiate(payment: dict, **_) -> dict:
    if config.PAYMENTS_MODE != "live":
        return {
            "status": "pending",
            "provider_reference": f"CAC-SANDBOX-{uuid.uuid4().hex[:10].upper()}",
            "instructions": (
                f"[SANDBOX] Paiement CAC Pay de {payment['amount_usd']:.2f} USD "
                f"initié. Validez la transaction dans votre application CAC Pay."
            ),
        }

    import requests

    if not (config.CACBANK_API_URL and config.CACBANK_MERCHANT_ID and config.CACBANK_API_KEY):
        raise RuntimeError("Identifiants CAC Bank manquants (CACBANK_API_URL, "
                           "CACBANK_MERCHANT_ID, CACBANK_API_KEY).")

    resp = requests.post(
        f"{config.CACBANK_API_URL.rstrip('/')}/payments",
        headers={"Authorization": f"Bearer {config.CACBANK_API_KEY}"},
        json={
            "merchant_id": config.CACBANK_MERCHANT_ID,
            "reference": payment["reference"],
            "amount": f"{payment['amount_usd']:.2f}",
            "currency": "USD",
            "description": f"Xeer AI — abonnement {payment['plan']}",
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    return {
        "status": "pending",
        "provider_reference": str(data.get("transaction_id", "")),
        "instructions": data.get("message", "Paiement initié — validez dans CAC Pay."),
    }
