"""Intégration WaafiPay (Waafi mobile money — Djibouti / Somalie).

En mode sandbox (défaut), le paiement est simulé et doit être confirmé via
POST /api/billing/confirm. En mode live, l'API WaafiPay est appelée avec les
identifiants marchands (WAAFI_MERCHANT_UID, WAAFI_API_USER_ID, WAAFI_API_KEY).
Documentation : https://developer.waafipay.com
"""
import uuid

from app import config


def initiate(payment: dict, *, phone: str = "", **_) -> dict:
    """Lance un paiement. Retourne {status, provider_reference, instructions}."""
    if config.PAYMENTS_MODE != "live":
        return {
            "status": "pending",
            "provider_reference": f"WFP-SANDBOX-{uuid.uuid4().hex[:10].upper()}",
            "instructions": (
                f"[SANDBOX] Une demande de paiement Waafi de "
                f"{payment['amount_usd']:.2f} USD a été envoyée au "
                f"{phone or 'numéro fourni'}. Confirmez sur votre téléphone."
            ),
        }

    import requests

    if not (config.WAAFI_MERCHANT_UID and config.WAAFI_API_USER_ID and config.WAAFI_API_KEY):
        raise RuntimeError("Identifiants WaafiPay manquants (WAAFI_MERCHANT_UID, "
                           "WAAFI_API_USER_ID, WAAFI_API_KEY).")

    payload = {
        "schemaVersion": "1.0",
        "requestId": payment["reference"],
        "timestamp": payment["created_at"],
        "channelName": "WEB",
        "serviceName": "API_PURCHASE",
        "serviceParams": {
            "merchantUid": config.WAAFI_MERCHANT_UID,
            "apiUserId": config.WAAFI_API_USER_ID,
            "apiKey": config.WAAFI_API_KEY,
            "paymentMethod": "MWALLET_ACCOUNT",
            "payerInfo": {"accountNo": phone},
            "transactionInfo": {
                "referenceId": payment["reference"],
                "invoiceId": payment["reference"],
                "amount": f"{payment['amount_usd']:.2f}",
                "currency": "USD",
                "description": f"Xeer AI — abonnement {payment['plan']}",
            },
        },
    }
    resp = requests.post(config.WAAFI_API_URL, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    ok = str(data.get("responseCode")) == "2001"
    return {
        "status": "completed" if ok else "failed",
        "provider_reference": str(data.get("params", {}).get("transactionId", "")),
        "instructions": data.get("responseMsg", ""),
    }
