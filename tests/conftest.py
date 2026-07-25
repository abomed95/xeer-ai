"""Configuration commune des tests.

Les tests tournent sur SQLite par défaut (aucun service à lancer). Pour les
exécuter sur PostgreSQL — la base de production — définis `DATABASE_URL` :

    DATABASE_URL=postgresql://... pytest

Chaque test part d'une base vierge et de compteurs de débit remis à zéro.
"""
import os
import tempfile
import uuid
from pathlib import Path

import pytest

# Configuration d'environnement AVANT l'import de l'application : app.config
# lit les variables au chargement du module.
os.environ.setdefault("XEER_DEMO_MODE", "1")
os.environ.setdefault("XEER_SECRET_KEY", "cle-de-test-suffisamment-longue-pour-les-controles-32")
os.environ.setdefault("XEER_ADMIN_EMAIL", "admin@xeer.ai")
os.environ.setdefault("XEER_ADMIN_PASSWORD", "MotDePasseAdminDeTest2026")
os.environ.setdefault("XEER_PAYMENTS_MODE", "sandbox")

_TMP_DB = Path(tempfile.gettempdir()) / f"xeer_test_{uuid.uuid4().hex}.db"
if not os.environ.get("DATABASE_URL"):
    os.environ["XEER_DATABASE_PATH"] = str(_TMP_DB)

ADMIN_EMAIL = os.environ["XEER_ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["XEER_ADMIN_PASSWORD"]


@pytest.fixture(scope="session", autouse=True)
def _cleanup_sqlite():
    yield
    _TMP_DB.unlink(missing_ok=True)


@pytest.fixture
def client():
    """Client de test avec une base vierge et les compteurs de débit remis à zéro."""
    from fastapi.testclient import TestClient

    from app import ratelimit
    from app.database import get_db, init_db
    from app.main import app

    init_db()  # garantit l'existence des tables avant le nettoyage
    # Base vierge : l'ordre de suppression respecte les clés étrangères.
    with get_db() as db:
        for table in ("messages", "conversations", "questions_log", "payments",
                      "org_leads", "users"):
            db.execute(f"DELETE FROM {table}")
    ratelimit.reset()

    with TestClient(app) as test_client:
        yield test_client

    ratelimit.reset()


@pytest.fixture
def user_token(client):
    """Crée un compte client et renvoie son en-tête d'authentification."""
    response = client.post("/api/auth/register", json={
        "email": "client@xeer.ai",
        "password": "MotDePasseClient2026",
        "full_name": "Client de test",
    })
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}


@pytest.fixture
def admin_token(client):
    """En-tête d'authentification du compte administrateur initial."""
    response = client.post("/api/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
    })
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['token']}"}
