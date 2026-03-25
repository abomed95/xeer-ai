from typing import List, Dict, Any
import re

import chromadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer

# ===== CONFIG =====
DB_DIR = "chroma_db"
COLLECTION_NAME = "xeer_chunks"
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# ===== APP =====
app = FastAPI(
    title="Xeer AI API",
    description="API RAG pour interroger le livre Xeer Ciise",
    version="1.0.0",
)

# ===== GLOBALS =====
model = None
client = None
collection = None


# ===== SCHEMAS =====
class AskRequest(BaseModel):
    question: str
    top_k: int = 8


class SourceItem(BaseModel):
    id: str
    page: str
    chunk_index: int | None = None
    source_file: str | None = None
    distance: float
    score: int
    excerpt: str


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: List[SourceItem]


# ===== HELPERS =====
def load_dependencies():
    global model, client, collection

    if model is None:
        model = SentenceTransformer(MODEL_NAME)

    if client is None:
        client = chromadb.PersistentClient(path=DB_DIR)

    if collection is None:
        try:
            collection = client.get_collection(COLLECTION_NAME)
        except Exception as exc:
            raise RuntimeError(
                f"Collection '{COLLECTION_NAME}' introuvable. "
                f"Exécute d'abord: python scripts/build_vector_store.py"
            ) from exc


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

    query_embedding = model.encode([query]).tolist()[0]

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


def generate_simple_answer(question: str, results: List[Dict[str, Any]]) -> str:
    if not results:
        return "Wax jawaab ku filan lagama helin xogta hadda la geliyey."

    best_doc = results[0]["doc"]

    # enlève la ligne de préfixe "Bogga xxx - Xeer Ciise"
    lines = [line.strip() for line in best_doc.splitlines() if line.strip()]
    if lines and lines[0].lower().startswith("bogga"):
        lines = lines[1:]

    summary = " ".join(lines)
    summary = re.sub(r"\s+", " ", summary).strip()

    if len(summary) > 700:
        summary = summary[:700] + "..."

    return (
        f"Jawaab kooban: {summary}\n\n"
        f"Su'aasha: {question}\n"
        f"Xigashada ugu muhiimsan: bogga {results[0]['meta'].get('page', 'N/A')}."
    )


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
    }


@app.get("/health")
def health():
    try:
        load_dependencies()
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest):
    question = payload.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question vide.")

    try:
        results = search_xeer(question, n_results=payload.top_k)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    answer = generate_simple_answer(question, results)

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
        question=question,
        answer=answer,
        sources=sources,
    )