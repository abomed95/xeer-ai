"""Parcours client de bout en bout : comptes, chat, quotas, paiement, admin."""


def test_health_expose_l_etat_du_deploiement(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    # Champs de diagnostic d'un déploiement (voir docs/DEPLOY_DIGITALOCEAN.md).
    for champ in ("demo_mode", "openai_key_set", "rag_ready", "database",
                  "persistent_storage", "llm_model"):
        assert champ in body, champ


def test_modele_openai_par_defaut_est_reel(client):
    """Un modèle inexistant (ex. gpt-5.6) fait échouer toute requête réelle."""
    modele = client.get("/api/health").json()["llm_model"]
    assert modele.startswith("gpt-4o") or modele.startswith("gpt-4."), modele


class TestAuthentification:
    def test_inscription_et_connexion(self, client):
        response = client.post("/api/auth/register", json={
            "email": "nouveau@xeer.ai", "password": "MotDePasse2026",
            "full_name": "Nouveau Client"})
        assert response.status_code == 200
        assert response.json()["token"]

        response = client.post("/api/auth/login", json={
            "email": "nouveau@xeer.ai", "password": "MotDePasse2026"})
        assert response.status_code == 200

    def test_email_deja_utilise_est_refuse(self, client, user_token):
        response = client.post("/api/auth/register", json={
            "email": "client@xeer.ai", "password": "MotDePasse2026",
            "full_name": "Doublon"})
        assert response.status_code == 409

    def test_mauvais_mot_de_passe_est_refuse(self, client, user_token):
        response = client.post("/api/auth/login", json={
            "email": "client@xeer.ai", "password": "mauvais"})
        assert response.status_code == 401

    def test_acces_sans_jeton_est_refuse(self, client):
        assert client.get("/api/auth/me").status_code == 401

    def test_jeton_invalide_est_refuse(self, client):
        response = client.get("/api/auth/me",
                              headers={"Authorization": "Bearer nimporte.quoi"})
        assert response.status_code == 401

    def test_profil_et_changement_de_mot_de_passe(self, client, user_token):
        response = client.put("/api/auth/profile", json={"full_name": "Nom Modifié"},
                              headers=user_token)
        assert response.status_code == 200
        assert response.json()["full_name"] == "Nom Modifié"

        response = client.put("/api/auth/password", json={
            "current_password": "MotDePasseClient2026",
            "new_password": "NouveauMotDePasse2026"}, headers=user_token)
        assert response.status_code == 200
        assert client.post("/api/auth/login", json={
            "email": "client@xeer.ai",
            "password": "NouveauMotDePasse2026"}).status_code == 200


class TestChatEtQuotas:
    def test_question_renvoie_une_reponse_sourcee(self, client, user_token):
        response = client.post("/api/chat/ask", json={"question": "Waa maxay xeer?"},
                               headers=user_token)
        assert response.status_code == 200
        body = response.json()
        assert body["answer"]
        assert body["conversation_id"]
        assert body["sources"], "une réponse doit citer ses sources"

    def test_question_vide_est_refusee(self, client, user_token):
        response = client.post("/api/chat/ask", json={"question": "   "},
                               headers=user_token)
        assert response.status_code == 400

    def test_quota_gratuit_bloque_a_la_quatrieme_question(self, client, user_token):
        for numero in range(3):
            response = client.post("/api/chat/ask",
                                   json={"question": f"Question {numero}"},
                                   headers=user_token)
            assert response.status_code == 200, response.text
        # Le plan gratuit autorise 3 questions par mois.
        response = client.post("/api/chat/ask", json={"question": "Une de trop"},
                               headers=user_token)
        assert response.status_code == 402

    def test_historique_est_persiste(self, client, user_token):
        premiere = client.post("/api/chat/ask", json={"question": "Première"},
                               headers=user_token).json()
        conversation = premiere["conversation_id"]
        client.post("/api/chat/ask",
                    json={"question": "Suite", "conversation_id": conversation},
                    headers=user_token)

        response = client.get(f"/api/chat/conversations/{conversation}",
                              headers=user_token)
        assert response.status_code == 200
        # 2 échanges = 2 questions + 2 réponses
        assert len(response.json()["messages"]) == 4

    def test_conversation_d_autrui_est_inaccessible(self, client, user_token):
        conversation = client.post("/api/chat/ask", json={"question": "Privée"},
                                   headers=user_token).json()["conversation_id"]
        autre = client.post("/api/auth/register", json={
            "email": "autre@xeer.ai", "password": "MotDePasse2026",
            "full_name": "Autre"}).json()
        entete = {"Authorization": f"Bearer {autre['token']}"}
        assert client.get(f"/api/chat/conversations/{conversation}",
                          headers=entete).status_code == 404

    def test_feedback_sur_une_reponse(self, client, user_token):
        conversation = client.post("/api/chat/ask", json={"question": "Notée"},
                                   headers=user_token).json()["conversation_id"]
        messages = client.get(f"/api/chat/conversations/{conversation}",
                              headers=user_token).json()["messages"]
        identifiant = next(m["id"] for m in messages if m["role"] == "assistant")

        assert client.post(f"/api/chat/messages/{identifiant}/feedback",
                           json={"rating": 1}, headers=user_token).status_code == 200
        # Seules les valeurs 1 et -1 sont acceptées.
        assert client.post(f"/api/chat/messages/{identifiant}/feedback",
                           json={"rating": 5}, headers=user_token).status_code == 400


class TestPaiement:
    def test_paiement_sandbox_active_le_premium(self, client, user_token):
        reference = client.post("/api/billing/checkout",
                                json={"provider": "waafi", "phone": "+25277123456"},
                                headers=user_token).json()["reference"]

        response = client.post("/api/billing/confirm", json={"reference": reference},
                               headers=user_token)
        assert response.status_code == 200
        assert response.json()["status"] == "completed"

        profil = client.get("/api/auth/me", headers=user_token).json()
        assert profil["plan"] == "premium"
        assert profil["quota"] is None, "Premium doit être illimité"

    def test_premium_leve_la_limite_de_quota(self, client, user_token):
        reference = client.post("/api/billing/checkout",
                                json={"provider": "waafi", "phone": "+25277123456"},
                                headers=user_token).json()["reference"]
        client.post("/api/billing/confirm", json={"reference": reference},
                    headers=user_token)
        # Au-delà des 3 questions du plan gratuit.
        for numero in range(5):
            response = client.post("/api/chat/ask",
                                   json={"question": f"Illimitée {numero}"},
                                   headers=user_token)
            assert response.status_code == 200, response.text

    def test_paiement_d_autrui_est_inconfirmable(self, client, user_token):
        reference = client.post("/api/billing/checkout",
                                json={"provider": "waafi", "phone": "+25277123456"},
                                headers=user_token).json()["reference"]
        autre = client.post("/api/auth/register", json={
            "email": "voleur@xeer.ai", "password": "MotDePasse2026",
            "full_name": "Voleur"}).json()
        entete = {"Authorization": f"Bearer {autre['token']}"}
        assert client.post("/api/billing/confirm", json={"reference": reference},
                           headers=entete).status_code == 404

    def test_historique_des_paiements(self, client, user_token):
        client.post("/api/billing/checkout",
                    json={"provider": "waafi", "phone": "+25277123456"},
                    headers=user_token)
        response = client.get("/api/billing/history", headers=user_token)
        assert response.status_code == 200
        assert len(response.json()["payments"]) == 1

    def test_demande_de_devis_organisation(self, client):
        response = client.post("/api/billing/org-lead", json={
            "name": "Directeur", "email": "dir@org.dj",
            "organization": "Ministère", "message": "50 comptes"})
        assert response.status_code == 200


class TestAdministration:
    def test_client_ne_peut_pas_acceder_a_l_admin(self, client, user_token):
        assert client.get("/api/admin/stats", headers=user_token).status_code == 403

    def test_statistiques_refletent_l_activite(self, client, user_token, admin_token):
        client.post("/api/chat/ask", json={"question": "Comptée"}, headers=user_token)
        reference = client.post("/api/billing/checkout",
                                json={"provider": "waafi", "phone": "+25277123456"},
                                headers=user_token).json()["reference"]
        client.post("/api/billing/confirm", json={"reference": reference},
                    headers=user_token)

        stats = client.get("/api/admin/stats", headers=admin_token).json()
        assert stats["questions"]["total"] >= 1
        assert stats["revenue"]["total_usd"] == 10.0
        assert stats["users"]["premium_active"] == 1
        assert stats["revenue"]["mrr_usd"] == 10.0
        # Séries 30 jours : requêtes substr(), sensibles au moteur de base.
        assert stats["series"]["questions_daily"]
        assert stats["series"]["revenue_daily"]

    def test_liste_et_recherche_d_utilisateurs(self, client, user_token, admin_token):
        assert client.get("/api/admin/users", headers=admin_token).status_code == 200
        # Recherche par LIKE
        response = client.get("/api/admin/users?q=client", headers=admin_token)
        assert response.status_code == 200
        assert any(u["email"] == "client@xeer.ai" for u in response.json()["users"])

    def test_paiements_et_leads_visibles(self, client, admin_token):
        assert client.get("/api/admin/payments", headers=admin_token).status_code == 200
        assert client.get("/api/admin/leads", headers=admin_token).status_code == 200
