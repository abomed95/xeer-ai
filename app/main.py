from typing import List, Dict, Any
import os
import re
from uuid import uuid4

import chromadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv
from openai import OpenAI

# ===== LOAD ENV =====
load_dotenv()

# ===== CONFIG =====
DB_DIR = "chroma_db"
COLLECTION_NAME = "xeer_chunks"
EMBED_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_HISTORY_MESSAGES = 6  # 3 échanges user/assistant

# ===== APP =====
app = FastAPI(
    title="Xeer AI API",
    description="API RAG pour interroger le livre Xeer Ciise",
    version="3.0.0",
)

# ===== GLOBALS =====
embed_model = None
client_db = None
collection = None
openai_client = None

# mémoire simple en RAM
conversation_memory: Dict[str, List[Dict[str, str]]] = {}


# ===== SCHEMAS =====
class AskRequest(BaseModel):
    question: str
    top_k: int = 5
    session_id: str | None = None


class SourceItem(BaseModel):
    id: str
    page: str
    chunk_index: int | None = None
    source_file: str | None = None
    distance: float
    score: int
    excerpt: str


class AskResponse(BaseModel):
    session_id: str
    question: str
    answer: str
    sources: List[SourceItem]


# ===== HELPERS =====
def load_dependencies():
    global embed_model, client_db, collection, openai_client

    if embed_model is None:
        embed_model = SentenceTransformer(EMBED_MODEL_NAME)

    if client_db is None:
        client_db = chromadb.PersistentClient(path=DB_DIR)

    if collection is None:
        try:
            collection = client_db.get_collection(COLLECTION_NAME)
        except Exception as exc:
            raise RuntimeError(
                f"Collection '{COLLECTION_NAME}' introuvable. "
                f"Exécute d'abord: python scripts/build_vector_store.py"
            ) from exc

    if openai_client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY introuvable dans .env")
        openai_client = OpenAI(api_key=api_key)


def is_bad_result(text: str) -> bool:
    text_lower = text.lower()

    if len(text.strip()) < 120:
        return True

    digits = sum(c.isdigit() for c in text)
    if digits > 20:
        return True

    if text.count(")") > 10:
        return True

    bad_words = ["daabacaad", "xuquuqda", "isbn", "tifaftirka"]
    if any(word in text_lower for word in bad_words):
        return True

    return False


def keyword_score(query: str, text: str) -> int:
    score = 0
    query_words = query.lower().split()
    text_lower = text.lower()

    for word in query_words:
        if word in text_lower:
            score += 1

    return score


def search_xeer(query: str, n_results: int = 8) -> List[Dict[str, Any]]:
    load_dependencies()

    query_embedding = embed_model.encode([query]).tolist()[0]

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )

    docs = results["documents"][0]
    metas = results["metadatas"][0]
    distances = results["distances"][0]
    ids = results["ids"][0]

    final_results = []

    for doc, meta, dist, doc_id in zip(docs, metas, distances, ids):
        if is_bad_result(doc):
            continue

        score = keyword_score(query, doc)

        final_results.append({
            "id": doc_id,
            "doc": doc,
            "meta": meta,
            "dist": float(dist),
            "score": score,
        })

    final_results = sorted(
        final_results,
        key=lambda x: (x["dist"], -x["score"])
    )

    return final_results[:5]


def clean_excerpt(text: str, max_len: int = 500) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len] + ("..." if len(text) > max_len else "")


def build_context(results: List[Dict[str, Any]]) -> str:
    parts = []
    for i, r in enumerate(results, start=1):
        page = r["meta"].get("page", "N/A")
        parts.append(f"[Source {i} - Bogga {page}]\n{r['doc']}")
    return "\n\n".join(parts)


def get_or_create_session_id(session_id: str | None) -> str:
    return session_id.strip() if session_id and session_id.strip() else str(uuid4())


def get_history(session_id: str) -> List[Dict[str, str]]:
    return conversation_memory.get(session_id, [])


def save_to_history(session_id: str, user_question: str, assistant_answer: str):
    if session_id not in conversation_memory:
        conversation_memory[session_id] = []

    conversation_memory[session_id].append({
        "role": "user",
        "content": user_question
    })
    conversation_memory[session_id].append({
        "role": "assistant",
        "content": assistant_answer
    })

    # garder seulement les derniers messages
    conversation_memory[session_id] = conversation_memory[session_id][-MAX_HISTORY_MESSAGES:]


def generate_openai_answer(question: str, results: List[Dict[str, Any]], history: List[Dict[str, str]]) -> str:
    if not results:
        return "Wax jawaab ku filan lagama helin xogta hadda la geliyey."

    load_dependencies()
    context = build_context(results)

    system_prompt = """
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

    messages = [{"role": "system", "content": system_prompt}]

    if history:
        messages.append({
            "role": "system",
            "content": "Kuwani waa farriimihii ugu dambeeyey ee wada hadalka si aad u ilaaliso macnaha guud."
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

    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=messages,
        temperature=0.1,
        max_tokens=350,
    )

    return response.choices[0].message.content.strip()


# ===== EVENTS =====
@app.on_event("startup")
def startup_event():
    load_dependencies()


# ===== ROUTES =====
@app.get("/")
def root():
    return {
        "message": "Xeer AI API is running",
        "collection": COLLECTION_NAME,
        "llm_model": OPENAI_MODEL,
    }


@app.get("/health")
def health():
    try:
        load_dependencies()
        return {"status": "ok", "llm_model": OPENAI_MODEL}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/sessions/{session_id}")
def get_session_messages(session_id: str):
    return {
        "session_id": session_id,
        "history": get_history(session_id)
    }


@app.delete("/sessions/{session_id}")
def clear_session(session_id: str):
    if session_id in conversation_memory:
        del conversation_memory[session_id]
    return {
        "message": "Session supprimée",
        "session_id": session_id
    }


@app.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest):
    question = payload.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question vide.")

    session_id = get_or_create_session_id(payload.session_id)

    try:
        results = search_xeer(question, n_results=payload.top_k)
        history = get_history(session_id)
        answer = generate_openai_answer(question, results, history)
        save_to_history(session_id, question, answer)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    sources = [
        SourceItem(
            id=r["id"],
            page=str(r["meta"].get("page", "")),
            chunk_index=r["meta"].get("chunk_index"),
            source_file=r["meta"].get("source_file"),
            distance=r["dist"],
            score=r["score"],
            excerpt=clean_excerpt(r["doc"]),
        )
        for r in results
    ]

    return AskResponse(
        session_id=session_id,
        question=question,
        answer=answer,
        sources=sources,
    )