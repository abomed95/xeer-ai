"""Moteur RAG : recherche sémantique sur le corpus Xeer + génération OpenAI.

Les dépendances lourdes (chromadb, sentence-transformers, openai) sont
importées paresseusement pour que l'API démarre sans elles ; en mode démo
(XEER_DEMO_MODE=1) les réponses sont simulées.
"""
import re
from typing import Any

from app import config

_embed_model = None
_client_db = None
_collection = None
_openai_client = None


def index_ready() -> bool:
    """Vrai si un index vectoriel semble présent sur disque (contrôle léger).

    Volontairement sans import de chromadb : sert au diagnostic /api/health.
    """
    from pathlib import Path

    db_dir = Path(config.DB_DIR)
    return db_dir.is_dir() and any(db_dir.iterdir())


def model_cached() -> bool:
    """Vrai si le modèle d'embeddings est présent en cache local.

    Si faux en production, la première question déclenche un téléchargement de
    ~460 Mo depuis HuggingFace : lenteur et dépendance externe.
    """
    from pathlib import Path

    cache = Path(config.MODEL_CACHE_DIR)
    if not cache.is_dir():
        return False
    return any(cache.rglob("*.safetensors")) or any(cache.rglob("pytorch_model.bin"))


def model_loaded() -> bool:
    """Vrai si le modèle est déjà chargé en mémoire (préchauffage terminé)."""
    return _embed_model is not None


def warm() -> None:
    """Précharge le moteur RAG en tâche de fond au démarrage.

    Sans cela, le premier client à poser une question paie le chargement du
    modèle. Les erreurs sont journalisées sans interrompre le service : l'appel
    suivant à /ask retentera et remontera l'erreur au client.
    """
    try:
        load_dependencies()
        print("[Xeer AI] Moteur RAG préchargé (modèle d'embeddings en mémoire).")
    except Exception as exc:  # noqa: BLE001 — diagnostic, ne doit rien casser
        print(f"[Xeer AI] ⚠️  Préchargement du moteur RAG impossible : {exc}")


def load_dependencies():
    global _embed_model, _client_db, _collection, _openai_client

    import chromadb
    from openai import OpenAI
    from sentence_transformers import SentenceTransformer

    if _embed_model is None:
        _embed_model = SentenceTransformer(config.EMBED_MODEL_NAME)

    if _client_db is None:
        _client_db = chromadb.PersistentClient(path=config.DB_DIR)

    if _collection is None:
        try:
            _collection = _client_db.get_collection(config.COLLECTION_NAME)
        except Exception as exc:
            raise RuntimeError(
                f"Collection '{config.COLLECTION_NAME}' introuvable. "
                f"Exécute d'abord: python scripts/build_vector_store.py"
            ) from exc

    if _openai_client is None:
        if not config.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY manquante. En local : renseigne-la dans .env. "
                "Sur DigitalOcean : App → Settings → Environment Variables."
            )
        _openai_client = OpenAI(api_key=config.OPENAI_API_KEY)


def is_bad_result(text: str) -> bool:
    text_lower = text.lower()
    if len(text.strip()) < 120:
        return True
    if sum(c.isdigit() for c in text) > 20:
        return True
    if text.count(")") > 10:
        return True
    bad_words = ["daabacaad", "xuquuqda", "isbn", "tifaftirka"]
    return any(word in text_lower for word in bad_words)


def keyword_score(query: str, text: str) -> int:
    text_lower = text.lower()
    return sum(1 for word in query.lower().split() if word in text_lower)


def search_xeer(query: str, n_results: int = 8) -> list[dict[str, Any]]:
    load_dependencies()

    query_embedding = _embed_model.encode([query]).tolist()[0]
    results = _collection.query(query_embeddings=[query_embedding], n_results=n_results)

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]
    ids = results["ids"][0]

    final_results = []
    for doc, meta, dist, doc_id in zip(docs, metas, distances, ids):
        if is_bad_result(doc):
            continue
        final_results.append({
            "id": doc_id,
            "doc": doc,
            "meta": meta,
            "dist": float(dist),
            "score": keyword_score(query, doc),
        })

    final_results.sort(key=lambda x: (x["dist"], -x["score"]))
    return final_results[:5]


def clean_excerpt(text: str, max_len: int = 500) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def build_context(results: list[dict[str, Any]]) -> str:
    parts = []
    for i, r in enumerate(results, start=1):
        page = r["meta"].get("page", "N/A")
        parts.append(f"[Source {i} - Bogga {page}]\n{r['doc']}")
    return "\n\n".join(parts)


# --------------------------------------------------------------------------
# Langue de réponse
# --------------------------------------------------------------------------
# Les extraits fournis au modèle sont intégralement en somali. Une consigne
# générale du type « réponds dans la langue de la question » ne suffit pas :
# une question en français ou en anglais, écrite dans le même alphabet que le
# somali, se fait aspirer par le contexte et reçoit une réponse en somali.
# (L'arabe y échappait, son écriture étant distincte.)
# La langue est donc déterminée ici, puis imposée nommément au modèle.

_ARABE_RE = re.compile(r"[؀-ۿ]")

# Mots-outils très fréquents et discriminants d'une langue à l'autre.
_MARQUEURS = {
    "so": {
        "waa", "maxay", "waxa", "waxaa", "sidee", "yaa", "xeer", "xeerka",
        "iyo", "oo", "ku", "ka", "uu", "ay", "aan", "doorka", "odayaasha",
        "odayaal", "magta", "diya", "beesha", "sharci", "dhaqan", "muxuu",
        "kuwa", "haddii", "loo", "laga", "yahay", "tahay",
    },
    "fr": {
        "quel", "quelle", "quels", "quelles", "comment", "pourquoi", "est",
        "sont", "que", "qu", "qui", "les", "des", "une", "dans", "le", "la",
        "du", "au", "aux", "pour", "avec", "sur", "role", "rôle", "règlement",
        "conflits", "droit", "coutumier", "explique", "signifie", "veut",
        "dire", "peux", "peut", "quest", "combien", "lorsque",
    },
    "en": {
        "what", "how", "why", "who", "when", "which", "the", "is", "are",
        "does", "do", "of", "in", "role", "elders", "law", "customary",
        "explain", "tell", "me", "about", "can", "you", "please", "and",
        "dispute", "disputes", "resolve", "resolving", "meaning",
    },
}

LANGUES = {
    "so": "somali (Soomaali)",
    "ar": "arabe (العربية)",
    "fr": "français",
    "en": "anglais (English)",
}

# Intitulés des trois sections, dans chaque langue.
_TITRES = {
    "so": ("Qeexid", "Sharaxaad", "Muhiimadda", "Xigasho"),
    "ar": ("التعريف", "الشرح", "الأهمية", "المرجع"),
    "fr": ("Définition", "Explication", "Importance", "Source"),
    "en": ("Definition", "Explanation", "Importance", "Citation"),
}

# Consigne finale, rédigée DANS la langue cible : un modèle suit bien mieux une
# instruction formulée dans la langue qu'on lui demande d'employer.
_CONSIGNE = {
    "so": "MUHIIM: jawaabta oo dhan ku qor AF-SOOMAALI oo keliya.",
    "ar": "مهم: اكتب إجابتك بالكامل باللغة العربية فقط.",
    "fr": "IMPORTANT : rédige la totalité de ta réponse en FRANÇAIS uniquement. "
          "Les sources sont en somali, mais la réponse doit être en français.",
    "en": "IMPORTANT: write your entire answer in ENGLISH only. "
          "The sources are in Somali, but the answer must be in English.",
}


def detect_language(question: str) -> str | None:
    """Langue de la question : 'so', 'ar', 'fr', 'en', ou None si indécidable.

    None laisse le modèle décider seul, plutôt que de lui imposer une langue
    erronée sur une question trop courte ou atypique.
    """
    if _ARABE_RE.search(question):
        return "ar"

    mots = set(re.findall(r"[a-zà-ÿ']+", question.lower()))
    scores = {code: len(mots & marqueurs) for code, marqueurs in _MARQUEURS.items()}
    meilleur = max(scores, key=scores.get)
    if scores[meilleur] == 0:
        return None
    # Égalité entre deux langues : trop ambigu pour trancher.
    if list(scores.values()).count(scores[meilleur]) > 1:
        return None
    return meilleur


def build_system_prompt(langue: str | None) -> str:
    """Consigne système, spécialisée pour la langue de réponse attendue."""
    if langue:
        definition, explication, importance, citation = _TITRES[langue]
        regle_langue = (
            f"- Rédige TOUTE ta réponse en {LANGUES[langue]}, sans exception, "
            f"y compris les titres de sections.\n"
            f"- Les sources sont en somali : tu dois les TRADUIRE et les "
            f"synthétiser en {LANGUES[langue]}, jamais les recopier telles quelles."
        )
        structure = (
            f"1. 🔹 {definition} — 1 à 2 lignes\n"
            f"2. 🔹 {explication} — développement concis\n"
            f"3. 🔹 {importance} — pourquoi c'est important"
        )
        fin = f"Termine par : 📌 {citation} : bogga XXX"
    else:
        regle_langue = (
            "- Réponds dans la langue exacte de la question de l'utilisateur.\n"
            "- Les sources sont en somali : traduis-les si la question est "
            "posée dans une autre langue."
        )
        structure = (
            "1. 🔹 Définition — 1 à 2 lignes\n"
            "2. 🔹 Explication — développement concis\n"
            "3. 🔹 Importance — pourquoi c'est important"
        )
        fin = "Termine par la citation de la page la plus pertinente : 📌 bogga XXX"

    return f"""Tu es un expert du Xeer Ciise, le droit coutumier somali.

Langue de la réponse :
{regle_langue}

Fidélité aux sources :
- Réponds UNIQUEMENT à partir des extraits fournis.
- N'invente jamais rien qui n'y figure pas.
- Tiens compte des échanges précédents pour comprendre le contexte.

Structure de la réponse, avec les titres dans la langue de réponse :
{structure}

Contraintes :
- Synthétise, ne recopie pas le texte brut.
- 6 à 10 lignes maximum.
- Les termes propres au Xeer (odayaal, magta, xeer…) restent en somali,
  suivis d'une courte explication dans la langue de réponse.

{fin}
"""


# Message affiché quand aucun extrait pertinent n'est trouvé, dans la langue
# de la question : il était auparavant toujours en somali.
_AUCUN_RESULTAT = {
    "so": "Wax jawaab ku filan lagama helin xogta hadda la geliyey.",
    "ar": "لم يتم العثور على معلومات كافية في المصادر المتاحة.",
    "fr": "Aucune information suffisante n'a été trouvée dans le corpus pour "
          "répondre à cette question.",
    "en": "No sufficient information was found in the corpus to answer this "
          "question.",
}


def generate_openai_answer(
    question: str,
    results: list[dict[str, Any]],
    history: list[dict[str, str]],
) -> str:
    langue = detect_language(question)

    if not results:
        return _AUCUN_RESULTAT.get(langue or "so", _AUCUN_RESULTAT["so"])

    load_dependencies()
    context = build_context(results)

    messages = [{"role": "system", "content": build_system_prompt(langue)}]
    if history:
        messages.append({
            "role": "system",
            "content": "Voici les derniers messages de la conversation, pour "
                       "que tu conserves le contexte. Ils n'imposent pas la "
                       "langue de ta réponse.",
        })
        messages.extend(history)

    rappel_langue = (
        f"\n{_CONSIGNE[langue]}\n" if langue else
        "\nRéponds dans la langue exacte de la question ci-dessus.\n"
    )

    user_prompt = f"""Question de l'utilisateur :
{question}

Extraits du corpus (en somali) :
{context}

Rappels :
- Structure en 3 parties, titres dans la langue de réponse
- Synthétise, n'invente rien hors des extraits
- Termine par la citation de la page la plus pertinente
{rappel_langue}"""
    messages.append({"role": "user", "content": user_prompt})

    try:
        response = _openai_client.chat.completions.create(
            model=config.OPENAI_MODEL,
            messages=messages,
            temperature=0.1,
            max_tokens=500,
        )
    except Exception as exc:  # openai.APIError, AuthenticationError, etc.
        raise RuntimeError(_openai_error_message(exc)) from exc

    return response.choices[0].message.content.strip()


def _openai_error_message(exc: Exception) -> str:
    """Traduit une erreur OpenAI en message clair et actionnable."""
    status = getattr(exc, "status_code", None)
    detail = str(exc)
    if status == 401 or "api_key" in detail.lower() or "authentication" in detail.lower():
        return (
            "Clé OpenAI invalide ou expirée (OPENAI_API_KEY). "
            "Vérifie la variable d'environnement sur ton déploiement."
        )
    if status == 404 or "model" in detail.lower() and "not" in detail.lower():
        return (
            f"Le modèle OpenAI '{config.OPENAI_MODEL}' est introuvable. "
            "Utilise un modèle réel (ex. gpt-4o-mini, gpt-4o) via OPENAI_MODEL."
        )
    if status == 429 or "rate limit" in detail.lower() or "quota" in detail.lower():
        return (
            "Quota OpenAI dépassé ou limite de débit atteinte. "
            "Vérifie la facturation de ton compte OpenAI et réessaie."
        )
    return f"Erreur lors de l'appel à l'API OpenAI : {detail}"


def demo_answer(question: str) -> tuple[str, list[dict[str, Any]]]:
    """Réponse simulée quand XEER_DEMO_MODE=1 (aucune dépendance externe)."""
    answer = (
        "🔹 Qeexid : (mode démo) Xeer Ciise waa nidaamka sharciga dhaqameed "
        "ee beesha Ciise.\n\n"
        "🔹 Sharaxaad : Cette réponse est générée en mode démonstration, sans "
        "moteur RAG ni OpenAI. En production, la réponse s'appuie sur le "
        "corpus numérisé du Xeer Ciise avec citations de pages.\n\n"
        "🔹 Muhiimadda : Le mode démo permet de tester l'application complète "
        "(comptes, quotas, paiements) sans clé API.\n\n"
        "📌 Xigasho: bogga 1 (démo)"
    )
    sources = [{
        "id": "demo-1",
        "doc": f"Extrait de démonstration pour la question : {question}",
        "meta": {"page": "1", "chunk_index": 0, "source_file": "demo.txt"},
        "dist": 0.0,
        "score": 1,
    }]
    return answer, sources


def answer_question(
    question: str, top_k: int, history: list[dict[str, str]]
) -> tuple[str, list[dict[str, Any]]]:
    """Point d'entrée unique : renvoie (réponse, résultats de recherche)."""
    if config.DEMO_MODE:
        return demo_answer(question)
    results = search_xeer(question, n_results=max(top_k, 8))
    answer = generate_openai_answer(question, results, history)
    return answer, results
