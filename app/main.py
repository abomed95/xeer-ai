"""Xeer AI — API principale.

Assistant IA du Xeer Ciise (droit coutumier somali) avec comptes utilisateurs,
abonnements (Gratuit / Premium 10 $ / Organisation), paiements Waafi, CAC Bank
et cartes Visa/MasterCard, et tableau de bord administrateur.
"""
import secrets
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app import config
from app.database import get_db, init_db, utcnow
from app.routers import admin, auth, billing, chat
from app.security import hash_password

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

app = FastAPI(
    title=f"{config.APP_NAME} API",
    description="API RAG pour interroger le livre Xeer Ciise — "
                "abonnements, paiements et administration.",
    version=config.APP_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(billing.router)
app.include_router(admin.router)


def seed_admin():
    """Crée le compte administrateur initial s'il n'existe pas encore."""
    with get_db() as db:
        existing = db.execute(
            "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
        ).fetchone()
        if existing:
            return
        password = config.ADMIN_PASSWORD or (
            config.DEMO_ADMIN_PASSWORD if config.DEMO_MODE else secrets.token_urlsafe(12)
        )
        db.execute(
            "INSERT INTO users (email, password_hash, full_name, role, plan, created_at) "
            "VALUES (?, ?, ?, 'admin', 'premium', ?)",
            (config.ADMIN_EMAIL, hash_password(password), "Administrateur", utcnow()),
        )
    if not config.ADMIN_PASSWORD and not config.DEMO_MODE:
        print(f"[Xeer AI] Compte admin créé : {config.ADMIN_EMAIL} / {password}")
        print("[Xeer AI] Définissez XEER_ADMIN_PASSWORD pour un mot de passe stable.")


@app.on_event("startup")
def startup_event():
    init_db()
    seed_admin()


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "demo_mode": config.DEMO_MODE,
        "payments_mode": config.PAYMENTS_MODE,
        "llm_model": config.OPENAI_MODEL,
    }


# Le frontend (landing, app, admin, PWA) est servi à la racine.
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
