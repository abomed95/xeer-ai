"""Tests de sécurité : signatures de webhook, limitation de débit, garde-fous.

Le test central est `test_webhook_non_signe_ne_peut_pas_activer_le_premium` : il
reproduit le contournement de paiement qui existait avant la vérification des
signatures — un client postait la référence obtenue à son checkout sur
l'endpoint de callback et obtenait Premium sans payer.
"""
import importlib
import json
import os

import pytest

from app import config, ratelimit
from app.services.payments import webhooks


def _checkout(client, entete) -> str:
    """Crée un paiement en attente et renvoie sa référence."""
    response = client.post("/api/billing/checkout",
                           json={"provider": "waafi", "phone": "+25277123456"},
                           headers=entete)
    assert response.status_code == 200, response.text
    return response.json()["reference"]


def _plan(client, entete) -> str:
    return client.get("/api/auth/me", headers=entete).json()["plan"]


class TestSignaturesDeWebhook:
    """Un callback non authentifié ne doit jamais activer un abonnement."""

    def test_webhook_non_signe_ne_peut_pas_activer_le_premium(
        self, client, user_token, monkeypatch
    ):
        # Un secret est configuré : la vérification est donc active.
        monkeypatch.setattr(config, "WAAFI_WEBHOOK_SECRET", "secret-partage-waafi")
        reference = _checkout(client, user_token)

        # Le client tente d'activer son abonnement lui-même, sans payer.
        response = client.post("/api/billing/webhook/waafi",
                               json={"reference": reference})
        assert response.status_code == 401, (
            "un callback sans signature doit être rejeté — sinon Premium gratuit"
        )
        assert _plan(client, user_token) == "free", "l'abonnement ne doit pas être activé"

    def test_signature_invalide_est_rejetee(self, client, user_token, monkeypatch):
        monkeypatch.setattr(config, "WAAFI_WEBHOOK_SECRET", "secret-partage-waafi")
        reference = _checkout(client, user_token)

        response = client.post("/api/billing/webhook/waafi",
                               json={"reference": reference},
                               headers={"x-waafi-signature": "0" * 64})
        assert response.status_code == 401
        assert _plan(client, user_token) == "free"

    def test_signature_valide_active_le_premium(self, client, user_token, monkeypatch):
        monkeypatch.setattr(config, "WAAFI_WEBHOOK_SECRET", "secret-partage-waafi")
        reference = _checkout(client, user_token)

        corps = json.dumps({"reference": reference}).encode()
        entetes = webhooks.sign("waafi", corps)
        response = client.post("/api/billing/webhook/waafi", content=corps,
                               headers={**entetes, "content-type": "application/json"})
        assert response.status_code == 200, response.text
        assert _plan(client, user_token) == "premium"

    def test_callback_rejoue_trop_tard_est_rejete(self, client, user_token, monkeypatch):
        monkeypatch.setattr(config, "WAAFI_WEBHOOK_SECRET", "secret-partage-waafi")
        monkeypatch.setattr(config, "WEBHOOK_TIMESTAMP_TOLERANCE", 300)
        reference = _checkout(client, user_token)

        corps = json.dumps({"reference": reference}).encode()
        # Signature authentique, mais horodatée d'il y a deux heures.
        entetes = webhooks.sign("waafi", corps, timestamp="1000000000")
        response = client.post("/api/billing/webhook/waafi", content=corps,
                               headers={**entetes, "content-type": "application/json"})
        assert response.status_code == 401
        assert _plan(client, user_token) == "free"

    def test_corps_modifie_apres_signature_est_rejete(self, client, user_token,
                                                      monkeypatch):
        monkeypatch.setattr(config, "WAAFI_WEBHOOK_SECRET", "secret-partage-waafi")
        reference = _checkout(client, user_token)

        # Signature calculée sur un corps, envoyée avec un autre.
        entetes = webhooks.sign("waafi", json.dumps({"reference": "AUTRE"}).encode())
        response = client.post("/api/billing/webhook/waafi",
                               content=json.dumps({"reference": reference}).encode(),
                               headers={**entetes, "content-type": "application/json"})
        assert response.status_code == 401
        assert _plan(client, user_token) == "free"

    def test_signature_stripe_valide_pour_les_cartes(self, client, user_token,
                                                     monkeypatch):
        monkeypatch.setattr(config, "CARD_WEBHOOK_SECRET", "secret-stripe")
        response = client.post("/api/billing/checkout",
                               json={"provider": "card", "card_number": "4242424242424242",
                                     "card_expiry": "12/30", "card_cvc": "123",
                                     "card_holder": "Client Test"},
                               headers=user_token)
        assert response.status_code == 200, response.text
        reference = response.json()["reference"]

        corps = json.dumps({"metadata": {"reference": reference}}).encode()
        entetes = webhooks.sign("card", corps)
        assert "stripe-signature" in entetes
        response = client.post("/api/billing/webhook/card", content=corps,
                               headers={**entetes, "content-type": "application/json"})
        assert response.status_code == 200, response.text
        assert _plan(client, user_token) == "premium"

    def test_mode_live_sans_secret_refuse_le_callback(self, client, user_token,
                                                     monkeypatch):
        """Mieux vaut refuser un vrai paiement que d'en accepter un faux."""
        monkeypatch.setattr(config, "PAYMENTS_MODE", "live")
        monkeypatch.setattr(config, "WAAFI_WEBHOOK_SECRET", "")
        response = client.post("/api/billing/webhook/waafi",
                               json={"reference": "XEER-INEXISTANT"})
        assert response.status_code == 503

    def test_fournisseur_inconnu_est_refuse(self, client):
        response = client.post("/api/billing/webhook/inconnu",
                               json={"reference": "XEER-TEST"})
        assert response.status_code == 404


class TestLimitationDeDebit:
    def test_bruteforce_de_connexion_est_bloque(self, client, user_token):
        ratelimit.reset()
        codes = [
            client.post("/api/auth/login",
                        json={"email": "client@xeer.ai", "password": f"essai{n}"}
                        ).status_code
            for n in range(12)
        ]
        assert 429 in codes, "le bruteforce doit finir par être bloqué"
        assert codes.count(401) <= 10, "au plus 10 essais avant blocage"

    def test_reponse_429_indique_le_delai_d_attente(self, client, user_token):
        ratelimit.reset()
        derniere = None
        for _ in range(15):
            derniere = client.post("/api/auth/login",
                                   json={"email": "client@xeer.ai", "password": "x"})
            if derniere.status_code == 429:
                break
        assert derniere.status_code == 429
        assert "Retry-After" in derniere.headers

    def test_creation_de_comptes_en_masse_est_bloquee(self, client):
        ratelimit.reset()
        codes = [
            client.post("/api/auth/register", json={
                "email": f"masse{n}@xeer.ai", "password": "MotDePasse2026",
                "full_name": f"Masse {n}"}).status_code
            for n in range(8)
        ]
        assert 429 in codes

    def test_abus_de_questions_est_bloque(self, client, user_token):
        """Chaque question coûte des crédits OpenAI : le débit est plafonné."""
        ratelimit.reset()
        reference = _checkout(client, user_token)
        client.post("/api/billing/confirm", json={"reference": reference},
                    headers=user_token)  # Premium : plus de quota mensuel

        codes = [
            client.post("/api/chat/ask", json={"question": f"Spam {n}"},
                        headers=user_token).status_code
            for n in range(25)
        ]
        assert 429 in codes, "le débit doit être plafonné même sans quota mensuel"

    def test_limite_par_utilisateur_n_affecte_pas_les_autres(self, client, user_token):
        ratelimit.reset()
        for _ in range(12):
            client.post("/api/auth/login",
                        json={"email": "client@xeer.ai", "password": "x"})
        # Un autre utilisateur, déjà authentifié, garde l'accès à /ask.
        response = client.post("/api/chat/ask", json={"question": "Légitime"},
                               headers=user_token)
        assert response.status_code == 200, response.text


class TestGardeFousDeProduction:
    """Contrôles refusant une mise en production non sûre."""

    def _config_isolee(self, monkeypatch, **variables):
        for cle, valeur in variables.items():
            monkeypatch.setenv(cle, valeur)
        monkeypatch.setenv("XEER_DEMO_MODE", "0")
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fausse-cle-de-test")
        return importlib.reload(config)

    def test_secret_par_defaut_refuse_en_production(self, monkeypatch):
        module = self._config_isolee(monkeypatch,
                                     XEER_SECRET_KEY="change-me-in-production")
        with pytest.raises(RuntimeError, match="XEER_SECRET_KEY"):
            module.check_production_config()
        importlib.reload(config)

    def test_secret_trop_court_refuse_en_production(self, monkeypatch):
        module = self._config_isolee(monkeypatch, XEER_SECRET_KEY="trop-court")
        with pytest.raises(RuntimeError, match="trop courte"):
            module.check_production_config()
        importlib.reload(config)

    def test_mot_de_passe_admin_de_demo_refuse_en_production(self, monkeypatch):
        module = self._config_isolee(
            monkeypatch,
            XEER_SECRET_KEY="une-cle-aleatoire-suffisamment-longue-pour-passer",
            XEER_ADMIN_PASSWORD="xeer-demo-2026",
        )
        with pytest.raises(RuntimeError, match="démonstration"):
            module.check_production_config()
        importlib.reload(config)

    def test_configuration_saine_est_acceptee(self, monkeypatch):
        module = self._config_isolee(
            monkeypatch,
            XEER_SECRET_KEY="une-cle-aleatoire-suffisamment-longue-pour-passer",
            XEER_ADMIN_PASSWORD="MotDePasseAdminSolide2026",
            DATABASE_URL="postgresql://exemple/xeer",
            XEER_PAYMENTS_MODE="live",
        )
        assert module.check_production_config() == []
        importlib.reload(config)

    def test_stockage_non_persistant_est_signale(self, monkeypatch):
        monkeypatch.delenv("DATABASE_URL", raising=False)
        module = self._config_isolee(
            monkeypatch,
            XEER_SECRET_KEY="une-cle-aleatoire-suffisamment-longue-pour-passer",
            XEER_ADMIN_PASSWORD="MotDePasseAdminSolide2026",
        )
        avertissements = " ".join(module.check_production_config())
        assert "DATABASE_URL" in avertissements
        importlib.reload(config)

    def test_mode_demo_tolere_les_valeurs_par_defaut(self, monkeypatch):
        """Un déploiement de démonstration ne doit pas être bloqué."""
        monkeypatch.setenv("XEER_DEMO_MODE", "1")
        monkeypatch.setenv("XEER_SECRET_KEY", "change-me-in-production")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        module = importlib.reload(config)
        assert module.check_production_config()  # avertit sans lever
        importlib.reload(config)


class TestIsolationDesDonnees:
    def test_message_d_autrui_ne_peut_pas_etre_note(self, client, user_token):
        conversation = client.post("/api/chat/ask", json={"question": "Privée"},
                                   headers=user_token).json()["conversation_id"]
        messages = client.get(f"/api/chat/conversations/{conversation}",
                              headers=user_token).json()["messages"]
        identifiant = next(m["id"] for m in messages if m["role"] == "assistant")

        autre = client.post("/api/auth/register", json={
            "email": "curieux@xeer.ai", "password": "MotDePasse2026",
            "full_name": "Curieux"}).json()
        entete = {"Authorization": f"Bearer {autre['token']}"}
        response = client.post(f"/api/chat/messages/{identifiant}/feedback",
                               json={"rating": 1}, headers=entete)
        assert response.status_code == 404

    def test_conversation_d_autrui_ne_peut_pas_etre_supprimee(self, client, user_token):
        conversation = client.post("/api/chat/ask", json={"question": "Privée"},
                                   headers=user_token).json()["conversation_id"]
        autre = client.post("/api/auth/register", json={
            "email": "destructeur@xeer.ai", "password": "MotDePasse2026",
            "full_name": "Destructeur"}).json()
        entete = {"Authorization": f"Bearer {autre['token']}"}
        assert client.delete(f"/api/chat/conversations/{conversation}",
                             headers=entete).status_code == 404
        # La conversation du propriétaire est intacte.
        assert client.get(f"/api/chat/conversations/{conversation}",
                          headers=user_token).status_code == 200
