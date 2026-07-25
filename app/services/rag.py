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


def load_dependencies():
    global _embed_model, _client_db, _collection, _openai_client
    import os

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
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY introuvable dans .env")
        _openai_client = OpenAI(api_key=api_key)


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


SYSTEM_PROMPT = """
Waxaad tahay khabiir ku takhasusay Xeer Ciise iyo dhaqanka Soomaaliyeed.
You are an expert on Xeer Ciise, the Somali customary law tradition.

Règles fondamentales :
- Réponds UNIQUEMENT à partir des informations trouvées dans les sources fournies.
- N'invente jamais rien qui ne figure pas dans les sources.
- Tiens compte des questions et réponses précédentes pour comprendre le contexte.
- Réponds toujours DANS LA LANGUE DE LA QUESTION : somali, arabe, français ou anglais.

Structure de la réponse (3 parties, avec les titres dans la langue de la question) :
1. 🔹 Définition — 1 à 2 lignes
   (somali : Qeexid · arabe : التعريف · anglais : Definition)
2. 🔹 Explication — développement concis
   (somali : Sharaxaad · arabe : الشرح · anglais : Explanation)
3. 🔹 Importance — pourquoi c'est important
   (somali : Muhiimadda · arabe : الأهمية · anglais : Importance)

Contraintes :
- Si la question fait suite à une question précédente, relie naturellement la réponse.
- Ne recopie pas le texte brut : synthétise et explique.
- 6 à 10 lignes maximum.
- Pour l'arabe, rédige en arabe standard moderne clair ; les termes somalis du
  Xeer (odayaal, diya, xeer…) restent en somali, suivis d'une courte glose.

Termine toujours par la citation de la page la plus pertinente :
📌 Xigasho / المرجع / Citation : bogga/page XXX
"""


def generate_openai_answer(
    question: str,
    results: list[dict[str, Any]],
    history: list[dict[str, str]],
) -> str:
    if not results:
        return "Wax jawaab ku filan lagama helin xogta hadda la geliyey."

    load_dependencies()
    context = build_context(results)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.append({
            "role": "system",
            "content": "Kuwani waa farriimihii ugu dambeeyey ee wada hadalka "
                       "si aad u ilaaliso macnaha guud.",
        })
        messages.extend(history)

    user_prompt = f"""
Question actuelle :
{question}

Sources :
{context}

Rappels :
- Réponds dans la langue de la question (somali, arabe, français ou anglais)
- Structure en 3 parties : Définition, Explication, Importance
- Si la question fait suite à une question précédente, relie naturellement
- Synthétise, n'invente rien hors des sources
- Termine par la citation de la page la plus pertinente
"""
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
