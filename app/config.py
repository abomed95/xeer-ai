"""Configuration centrale de Xeer AI (variables d'environnement)."""
import os

from dotenv import load_dotenv

load_dotenv()

# --- Général ---
APP_NAME = "Xeer AI"
APP_VERSION = "4.2.0"

# Clé de signature des jetons d'authentification. Avec la valeur par défaut,
# n'importe qui peut forger un jeton (y compris admin) : elle est donc refusée
# en production (voir check_production_config).
DEFAULT_SECRET_KEY = "change-me-in-production"
SECRET_KEY = os.getenv("XEER_SECRET_KEY", DEFAULT_SECRET_KEY)
TOKEN_TTL_HOURS = int(os.getenv("XEER_TOKEN_TTL_HOURS", "72"))

# Stockage : PostgreSQL si DATABASE_URL est fourni (base managée = données
# persistantes), sinon fichier SQLite local.
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
DATABASE_PATH = os.getenv("XEER_DATABASE_PATH", "xeer.db")

# Mode démo : /ask répond sans RAG ni OpenAI (utile pour tester l'app
# complète sans clé API ni index vectoriel). Auto-activé quand aucune clé
# OpenAI n'est configurée, pour qu'un déploiement de démonstration fonctionne
# toujours (chat simulé, aucune dépendance lourde requise).
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
# Démo demandée explicitement, à distinguer du repli automatique ci-dessous :
# un déploiement de production sans clé OpenAI retombe en démo, mais ne doit
# pas pour autant hériter des identifiants de démonstration.
DEMO_MODE_EXPLICIT = os.getenv("XEER_DEMO_MODE", "0") == "1"
DEMO_MODE = DEMO_MODE_EXPLICIT or not OPENAI_API_KEY

# --- RAG / LLM ---
DB_DIR = os.getenv("XEER_CHROMA_DIR", "chroma_db")
COLLECTION_NAME = "xeer_chunks"
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
# Modèle OpenAI réel utilisé par l'API (doit exister côté OpenAI).
# `gpt-4o-mini` est un bon défaut : multilingue (somali/arabe/français/anglais),
# économique et disponible. Passe à `gpt-4o` pour une qualité supérieure.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_HISTORY_MESSAGES = 6  # 3 échanges user/assistant

# --- Compte administrateur initial ---
ADMIN_EMAIL = os.getenv("XEER_ADMIN_EMAIL", "admin@xeer.ai")
ADMIN_PASSWORD = os.getenv("XEER_ADMIN_PASSWORD", "")
# Mot de passe admin par défaut en mode démo (si XEER_ADMIN_PASSWORD non défini) :
# garantit une connexion admin stable et identique sur toutes les instances.
DEMO_ADMIN_PASSWORD = "xeer-demo-2026"

# --- Abonnements ---
# quota = nombre de questions par mois (None = illimité)
PLANS = {
    "free": {
        "name": "Gratuit",
        "price_usd": 0,
        "quota": 3,
    },
    "premium": {
        "name": "Premium",
        "price_usd": 10,
        "quota": None,
    },
    "organization": {
        "name": "Organisation",
        "price_usd": None,  # prix négociable, fixé par l'admin
        "quota": None,
    },
}
PREMIUM_PRICE_USD = 10.0
SUBSCRIPTION_DAYS = 30

# --- Paiements ---
# Sandbox par défaut : les paiements sont simulés de bout en bout.
# Passer XEER_PAYMENTS_MODE=live avec les identifiants marchands pour la prod.
PAYMENTS_MODE = os.getenv("XEER_PAYMENTS_MODE", "sandbox")

# WaafiPay (Waafi / mobile money — Djibouti, Somalie)
WAAFI_API_URL = os.getenv("WAAFI_API_URL", "https://api.waafipay.net/asm")
WAAFI_MERCHANT_UID = os.getenv("WAAFI_MERCHANT_UID", "")
WAAFI_API_USER_ID = os.getenv("WAAFI_API_USER_ID", "")
WAAFI_API_KEY = os.getenv("WAAFI_API_KEY", "")

# CAC Bank (CAC Pay)
CACBANK_API_URL = os.getenv("CACBANK_API_URL", "")
CACBANK_MERCHANT_ID = os.getenv("CACBANK_MERCHANT_ID", "")
CACBANK_API_KEY = os.getenv("CACBANK_API_KEY", "")

# Cartes Visa / MasterCard (passerelle compatible Stripe)
CARD_GATEWAY_API_URL = os.getenv("CARD_GATEWAY_API_URL", "https://api.stripe.com/v1")
CARD_GATEWAY_SECRET_KEY = os.getenv("CARD_GATEWAY_SECRET_KEY", "")

# --- Secrets de signature des webhooks de paiement ---
# Un callback non signé permettrait d'activer un abonnement sans payer : il
# suffirait de poster la référence d'un paiement en attente. Chaque fournisseur
# signe donc ses callbacks avec un secret partagé, vérifié à la réception.
WAAFI_WEBHOOK_SECRET = os.getenv("WAAFI_WEBHOOK_SECRET", "")
CACBANK_WEBHOOK_SECRET = os.getenv("CACBANK_WEBHOOK_SECRET", "")
CARD_WEBHOOK_SECRET = os.getenv("CARD_WEBHOOK_SECRET", "")

# Tolérance de rejeu des webhooks horodatés (secondes).
WEBHOOK_TIMESTAMP_TOLERANCE = int(os.getenv("XEER_WEBHOOK_TOLERANCE", "300"))

# --- Limitation de débit ---
# Protège contre le bruteforce des mots de passe et l'abus de /ask (qui
# consomme des crédits OpenAI à chaque appel). Compteurs en mémoire, donc par
# instance : suffisant avec instance_count=1, à déporter vers Redis au-delà.
RATE_LIMIT_ENABLED = os.getenv("XEER_RATE_LIMIT_ENABLED", "1") == "1"

# --- Contrôles de sécurité au démarrage ---


def check_production_config() -> list[str]:
    """Vérifie la configuration de production. Lève si elle n'est pas sûre.

    Renvoie la liste des avertissements non bloquants. Ces contrôles évitent de
    mettre en ligne une plateforme facturant de vrais clients avec des secrets
    connus publiquement.
    """
    warnings: list[str] = []

    if DEMO_MODE:
        # Déploiement de démonstration : on informe sans bloquer.
        if SECRET_KEY == DEFAULT_SECRET_KEY:
            warnings.append(
                "XEER_SECRET_KEY non définie (valeur par défaut) — acceptable "
                "en démo, jamais en production."
            )
        return warnings

    # --- Production (une clé OpenAI est configurée) ---
    if SECRET_KEY == DEFAULT_SECRET_KEY:
        raise RuntimeError(
            "XEER_SECRET_KEY utilise la valeur par défaut : les jetons "
            "d'authentification seraient forgeables par n'importe qui, y compris "
            "en tant qu'administrateur. Définis une longue chaîne aléatoire, "
            "p.ex. :  python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
    if len(SECRET_KEY) < 32:
        raise RuntimeError(
            "XEER_SECRET_KEY trop courte (< 32 caractères) pour signer des "
            "jetons en production. Génère-en une longue et aléatoire."
        )
    if ADMIN_PASSWORD and ADMIN_PASSWORD == DEMO_ADMIN_PASSWORD:
        raise RuntimeError(
            f"XEER_ADMIN_PASSWORD vaut le mot de passe de démonstration "
            f"('{DEMO_ADMIN_PASSWORD}'), connu publiquement. Change-le avant "
            "d'ouvrir la plateforme à de vrais clients."
        )
    if not DATABASE_URL:
        warnings.append(
            "DATABASE_URL non définie : stockage SQLite local. Sur un PaaS, le "
            "disque est éphémère — comptes et paiements seront perdus au "
            "redéploiement. Branche une base PostgreSQL managée."
        )
    if PAYMENTS_MODE != "live":
        warnings.append(
            "XEER_PAYMENTS_MODE=sandbox : les paiements sont simulés, aucun "
            "encaissement réel."
        )
    return warnings
