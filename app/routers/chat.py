"""Routes de chat : questions au moteur RAG, avec quota par abonnement."""
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_current_user
from app.schemas import AskRequest, AskResponse, SourceItem
from app.services import rag
from app.services.accounts import log_question, questions_used_this_month, quota_for

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/ask", response_model=AskResponse)
def ask_question(payload: AskRequest, user: dict = Depends(get_current_user)):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question vide.")

    quota = quota_for(user)
    used = questions_used_this_month(user["id"])
    if quota is not None and used >= quota:
        raise HTTPException(
            status_code=402,
            detail=(
                f"Quota gratuit atteint ({quota} questions/mois). "
                "Passez à Xeer AI Premium (10 $/mois) pour un accès illimité."
            ),
        )

    session_id = (payload.session_id or "").strip() or str(uuid4())

    try:
        answer, results = rag.answer_question(question, payload.top_k, session_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    log_question(user["id"], question)
    used += 1

    sources = [
        SourceItem(
            id=r["id"],
            page=str(r["meta"].get("page", "")),
            chunk_index=r["meta"].get("chunk_index"),
            source_file=r["meta"].get("source_file"),
            distance=r["dist"],
            score=r["score"],
            excerpt=rag.clean_excerpt(r["doc"]),
        )
        for r in results
    ]

    return AskResponse(
        session_id=session_id,
        question=question,
        answer=answer,
        sources=sources,
        questions_remaining=None if quota is None else max(0, quota - used),
    )


@router.get("/sessions/{session_id}")
def get_session_messages(session_id: str, user: dict = Depends(get_current_user)):
    return {"session_id": session_id, "history": rag.get_history(session_id)}


@router.delete("/sessions/{session_id}")
def clear_session(session_id: str, user: dict = Depends(get_current_user)):
    rag.clear_session(session_id)
    return {"message": "Session supprimée", "session_id": session_id}
