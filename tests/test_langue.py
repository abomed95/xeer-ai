"""La réponse doit être rédigée dans la langue de la question.

Les extraits transmis au modèle sont intégralement en somali. Sans consigne
explicite, une question posée en français ou en anglais — même alphabet que le
somali — recevait une réponse en somali. L'arabe y échappait grâce à son
écriture distincte.
"""
import pytest

from app.services import rag


class TestDetectionDeLangue:
    @pytest.mark.parametrize("question", [
        "Quel est le rôle des odayaal dans le règlement des conflits ?",
        "Comment est calculée la magta ?",
        "Qu'est-ce que le Xeer Ciise ?",
        "Explique le droit coutumier somali",
        "Pourquoi les odayaal sont-ils importants ?",
    ])
    def test_francais(self, question):
        assert rag.detect_language(question) == "fr"

    @pytest.mark.parametrize("question", [
        "What is the role of elders in resolving disputes?",
        "How does the Xeer law work?",
        "Explain the customary law about marriage",
    ])
    def test_anglais(self, question):
        assert rag.detect_language(question) == "en"

    @pytest.mark.parametrize("question", [
        "ما هو دور الشيوخ في حل النزاعات؟",
        "كيف تُحل النزاعات بين العائلات؟",
    ])
    def test_arabe(self, question):
        assert rag.detect_language(question) == "ar"

    @pytest.mark.parametrize("question", [
        "Waa maxay doorka odayaasha?",
        "Waa maxay xeerka guurka ee beesha Ciise?",
        "Sidee loo xisaabiyaa magta?",
        "Muxuu yahay Xeer Ciise?",
    ])
    def test_somali(self, question):
        assert rag.detect_language(question) == "so"

    def test_question_indecidable_ne_force_aucune_langue(self):
        """Mieux vaut laisser le modèle décider que lui imposer une erreur."""
        assert rag.detect_language("???") is None
        assert rag.detect_language("2026") is None

    def test_arabe_reconnu_meme_melange_a_du_latin(self):
        assert rag.detect_language("Xeer Ciise: ما هو التعريف؟") == "ar"


class TestConsigneDeLangue:
    @pytest.mark.parametrize("langue,attendu", [
        ("fr", "FRANÇAIS"), ("en", "ENGLISH"),
        ("so", "AF-SOOMAALI"), ("ar", "العربية"),
    ])
    def test_consigne_redigee_dans_la_langue_cible(self, langue, attendu):
        assert attendu in rag._CONSIGNE[langue]

    def test_prompt_nomme_la_langue_et_demande_la_traduction(self):
        prompt = rag.build_system_prompt("fr")
        assert "français" in prompt
        # Le modèle doit traduire les extraits, pas les recopier.
        assert "TRADUIRE" in prompt
        assert "Définition" in prompt and "Explication" in prompt

    @pytest.mark.parametrize("langue,titre", [
        ("so", "Qeexid"), ("ar", "التعريف"),
        ("fr", "Définition"), ("en", "Definition"),
    ])
    def test_titres_de_sections_dans_la_bonne_langue(self, langue, titre):
        assert titre in rag.build_system_prompt(langue)

    def test_langue_inconnue_laisse_le_modele_decider(self):
        prompt = rag.build_system_prompt(None)
        assert "langue exacte de la question" in prompt


class TestMessageSansResultat:
    """Ce message était toujours en somali, quelle que soit la question."""

    @pytest.mark.parametrize("langue,extrait", [
        ("fr", "Aucune information"),
        ("en", "No sufficient information"),
        ("ar", "لم يتم العثور"),
        ("so", "Wax jawaab"),
    ])
    def test_message_traduit(self, langue, extrait):
        assert extrait in rag._AUCUN_RESULTAT[langue]

    def test_aucun_resultat_repond_dans_la_langue_de_la_question(self):
        reponse = rag.generate_openai_answer(
            "Quel est le rôle des odayaal ?", [], []
        )
        assert "Aucune information" in reponse, (
            "une question en français doit obtenir un message en français"
        )

    def test_aucun_resultat_en_anglais(self):
        reponse = rag.generate_openai_answer(
            "What is the role of elders?", [], []
        )
        assert "No sufficient information" in reponse
