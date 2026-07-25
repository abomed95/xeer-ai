"""Configuration centrale de Xeer AI (variables d'environnement)."""
import os

from dotenv import load_dotenv

load_dotenv()

# --- Général ---
APP_NAME = "Xeer AI"
APP_VERSION = "4.2.0"
SECRET_KEY = os.getenv("XEER_SECRET_KEY", "change-me-in-production")
TOKEN_TTL_HOURS = int(os.getenv("XEER_TOKEN_TTL_HOURS", "72"))
DATABASE_PATH = os.getenv("XEER_DATABASE_PATH", "xeer.db")

# Mode démo : /ask répond sans RAG ni OpenAI (utile pour tester l'app
# complète sans clé API ni index vectoriel). Auto-activé quand aucune clé
# OpenAI n'est configurée, pour qu'un déploiement de démonstration fonctionne
# toujours (chat simulé, aucune dépendance lourde requise).
DEMO_MODE = (
    os.getenv("XEER_DEMO_MODE", "0") == "1"
    or not os.getenv("OPENAI_API_KEY", "").strip()
)

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
