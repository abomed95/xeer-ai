"""Registre des fournisseurs de paiement."""
from app.services.payments import cacbank, card, waafi

PROVIDERS = {
    "waafi": waafi,
    "cacbank": cacbank,
    "card": card,
}

# méthodes affichées côté client pour chaque fournisseur
PROVIDER_INFO = [
    {
        "id": "waafi",
        "name": "Waafi",
        "description": "Mobile money — Djibouti, Somalie, diaspora",
        "methods": ["waafi"],
        "requires_phone": True,
    },
    {
        "id": "cacbank",
        "name": "CAC Bank",
        "description": "CAC Pay / compte bancaire CAC International Bank",
        "methods": ["cacpay"],
        "requires_phone": False,
    },
    {
        "id": "card",
        "name": "Carte bancaire",
        "description": "Visa et MasterCard",
        "methods": ["visa", "mastercard"],
        "requires_phone": False,
    },
]


def get_provider(provider_id: str):
    provider = PROVIDERS.get(provider_id)
    if provider is None:
        raise ValueError(f"Fournisseur de paiement inconnu : {provider_id}")
    return provider
