"""Moteur RAG : recherche sémantique sur le corpus Xeer + génération OpenAI.

Les dépendances lourdes (chromadb, sentence-transformers, openai) sont
importées paresseusement pour que l'API démarre sans elles ; en mode démo
(XEER_DEMO_MODE=1) les réponses sont simulées.
"""
import re
from typing import Any

from app import config

# mémoire de conversation en RAM, par session
conversation_memory: dict[str, list[dict[str, str]]] = {}

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


def get_history(session_id: str) -> list[dict[str, str]]:
    return conversation_memory.get(session_id, [])


def save_to_history(session_id: str, user_question: str, assistant_answer: str):
    history = conversation_memory.setdefault(session_id, [])
    history.append({"role": "user", "content": user_question})
    history.append({"role": "assistant", "content": assistant_answer})
    conversation_memory[session_id] = history[-config.MAX_HISTORY_MESSAGES:]


def clear_session(session_id: str):
    conversation_memory.pop(session_id, None)


SYSTEM_PROMPT = """
Waxaad tahay khabiir ku takhasusay Xeer Ciise iyo dhaqanka Soomaaliyeed.

Waajibaadkaaga:
- Ka jawaab su'aalaha si cad, sax ah, oo kooban.
- Isticmaal kaliya macluumaadka laga helay sources-ka.
- Tixgeli su'aalihii iyo jawaabihii hore haddii ay jiraan si aad u fahanto macnaha guud.
- Ha samayn wax aan ku jirin xogta.

Qaabka jawaabta:
1. 🔹 Qeexid (Definition) — hal ilaa laba sadar
2. 🔹 Sharaxaad (Explanation) — faahfaahin kooban
3. 🔹 Muhiimadda (Importance) — sababta ay muhiim u tahay

Xeerar:
- Ku jawaab luqadda su'aasha
- Haddii su'aashu tahay su'aal daba socota, ku xir jawaabta wixii hore
- Ha ku darin wax ka baxsan sources-ka
- Jawaabta ha ka badnaan 6–8 sadar

Dhamaadka:
Ku dar:
📌 Xigasho: bogga XXX
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
Su'aasha hadda:
{question}

Sources:
{context}

Fadlan:
- Ka jawaab si nidaamsan
- Isticmaal 3 qaybood: Qeexid, Sharaxaad, Muhiimadda
- Haddii su'aashu ku xiran tahay su'aal hore, si dabiici ah u xiriiri
- Ha ku celin qoraalka sida uu yahay, balse soo koob oo sharax
- Ku dar tixraac bogga ugu muhiimsan
"""
    messages.append({"role": "user", "content": user_prompt})

    response = _openai_client.chat.completions.create(
        model=config.OPENAI_MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=350,
    )
    return response.choices[0].message.content.strip()


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
    question: str, top_k: int, session_id: str
) -> tuple[str, list[dict[str, Any]]]:
    """Point d'entrée unique : renvoie (réponse, résultats de recherche)."""
    if config.DEMO_MODE:
        answer, results = demo_answer(question)
    else:
        results = search_xeer(question, n_results=top_k)
        history = get_history(session_id)
        answer = generate_openai_answer(question, results, history)
    save_to_history(session_id, question, answer)
    return answer, results
