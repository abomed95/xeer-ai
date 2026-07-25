"""Vérification des callbacks (webhooks) des fournisseurs de paiement.

Sans vérification, l'endpoint de callback permet d'activer un abonnement sans
payer : il suffit de poster la référence d'un paiement en attente, référence que
le client reçoit lui-même au moment du checkout. Chaque fournisseur signe donc
ses callbacks avec un secret partagé, vérifié ici avant tout traitement.

Deux formats sont pris en charge :

* **HMAC simple** (Waafi, CAC Bank) — en-tête contenant le HMAC-SHA256
  hexadécimal du corps brut de la requête. Un en-tête d'horodatage facultatif
  (`X-Webhook-Timestamp`) active la protection contre le rejeu.
* **Format Stripe** (cartes Visa/MasterCard) — en-tête
  `Stripe-Signature: t=<horodatage>,v1=<hmac de "<horodatage>.<corps>">`,
  avec protection contre le rejeu obligatoire.
"""
import hashlib
import hmac
import time

from fastapi import HTTPException

from app import config

# provider_id -> (secret, en-tête de signature, format)
PROVIDERS = {
    "waafi": ("WAAFI_WEBHOOK_SECRET", "x-waafi-signature", "hmac"),
    "cacbank": ("CACBANK_WEBHOOK_SECRET", "x-cac-signature", "hmac"),
    "card": ("CARD_WEBHOOK_SECRET", "stripe-signature", "stripe"),
}


def _secret_for(provider_id: str) -> str:
    entry = PROVIDERS.get(provider_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Fournisseur inconnu.")
    return getattr(config, entry[0], "") or ""


def _check_timestamp(timestamp: str) -> None:
    """Rejette un callback trop ancien (protection contre le rejeu)."""
    try:
        sent_at = int(float(timestamp))
    except (TypeError, ValueError):
        raise HTTPException(status_code=401, detail="Horodatage de signature invalide.")
    if abs(time.time() - sent_at) > config.WEBHOOK_TIMESTAMP_TOLERANCE:
        raise HTTPException(status_code=401, detail="Callback expiré (rejeu possible).")


def _verify_hmac(secret: str, raw_body: bytes, headers, header_name: str) -> None:
    provided = headers.get(header_name, "")
    if not provided:
        raise HTTPException(
            status_code=401,
            detail=f"Signature manquante : en-tête {header_name} requis.",
        )

    timestamp = headers.get("x-webhook-timestamp", "")
    if timestamp:
        _check_timestamp(timestamp)
        signed_payload = f"{timestamp}.".encode() + raw_body
    else:
        signed_payload = raw_body

    expected = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    # compare_digest évite les attaques temporelles.
    if not hmac.compare_digest(expected, provided.strip().lower()):
        raise HTTPException(status_code=401, detail="Signature de callback invalide.")


def _verify_stripe(secret: str, raw_body: bytes, headers) -> None:
    header = headers.get("stripe-signature", "")
    if not header:
        raise HTTPException(
            status_code=401,
            detail="Signature manquante : en-tête Stripe-Signature requis.",
        )

    parts = dict(
        piece.split("=", 1) for piece in header.split(",") if "=" in piece
    )
    timestamp, provided = parts.get("t", ""), parts.get("v1", "")
    if not timestamp or not provided:
        raise HTTPException(status_code=401, detail="En-tête Stripe-Signature malformé.")

    _check_timestamp(timestamp)
    expected = hmac.new(
        secret.encode(), f"{timestamp}.".encode() + raw_body, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(expected, provided.strip().lower()):
        raise HTTPException(status_code=401, detail="Signature de callback invalide.")


def verify(provider_id: str, raw_body: bytes, headers) -> None:
    """Valide la signature d'un callback. Lève une HTTPException sinon.

    En mode `live`, un secret non configuré est une erreur de déploiement : on
    refuse le callback plutôt que de risquer une activation frauduleuse. En
    sandbox sans secret, la vérification est ignorée pour permettre les tests.
    """
    secret_attr, header_name, scheme = PROVIDERS[provider_id]
    secret = _secret_for(provider_id)

    if not secret:
        if config.PAYMENTS_MODE == "live":
            raise HTTPException(
                status_code=503,
                detail=(
                    f"{secret_attr} non configuré : impossible de vérifier les "
                    "callbacks de ce fournisseur. Callback refusé par sécurité."
                ),
            )
        return  # sandbox sans secret : vérification désactivée pour les tests

    if scheme == "stripe":
        _verify_stripe(secret, raw_body, headers)
    else:
        _verify_hmac(secret, raw_body, headers, header_name)


def sign(provider_id: str, raw_body: bytes, timestamp: str | None = None) -> dict[str, str]:
    """Génère les en-têtes signés d'un callback — utilisé par les tests.

    Permet de rejouer un callback authentique en local sans dépendre du
    fournisseur.
    """
    secret_attr, header_name, scheme = PROVIDERS[provider_id]
    secret = _secret_for(provider_id)
    timestamp = timestamp or str(int(time.time()))

    if scheme == "stripe":
        digest = hmac.new(
            secret.encode(), f"{timestamp}.".encode() + raw_body, hashlib.sha256
        ).hexdigest()
        return {"stripe-signature": f"t={timestamp},v1={digest}"}

    digest = hmac.new(
        secret.encode(), f"{timestamp}.".encode() + raw_body, hashlib.sha256
    ).hexdigest()
    return {header_name: digest, "x-webhook-timestamp": timestamp}
