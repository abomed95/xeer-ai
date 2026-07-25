"""Routes de chat : questions au moteur RAG, conversations persistées, feedback."""
from fastapi import APIRouter, Depends, HTTPException

from app import config
from app.deps import get_current_user
from app.ratelimit import rate_limit_user
from app.schemas import AskRequest, AskResponse, FeedbackRequest, SourceItem
from app.services import conversations, rag
from app.services.accounts import log_question, questions_used_this_month, quota_for

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/ask", response_model=AskResponse)
def ask_question(
    payload: AskRequest,
    # Chaque question consomme des crédits OpenAI : on plafonne le débit par
    # utilisateur (le quota mensuel ne protège pas les comptes illimités).
    user: dict = Depends(rate_limit_user("ask", limit=20, window_seconds=60)),
):
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

    # conversation existante (vérifiée) ou nouvelle
    conv_id = (payload.conversation_id or "").strip()
    if conv_id:
        if conversations.get_conversation(conv_id, user["id"]) is None:
            raise HTTPException(status_code=404, detail="Conversation introuvable.")
    else:
        conv_id = conversations.create_conversation(user["id"], title=question)

    history = conversations.history_for_llm(conv_id, config.MAX_HISTORY_MESSAGES)

    try:
        answer, results = rag.answer_question(question, payload.top_k, history)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
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
            excerpt=rag.clean_excerpt(r["doc"]),
        )
        for r in results
    ]

    conversations.add_message(conv_id, "user", question)
    message_id = conversations.add_message(
        conv_id, "assistant", answer, sources=[s.model_dump() for s in sources]
    )
    log_question(user["id"], question)
    used += 1

    return AskResponse(
        conversation_id=conv_id,
        message_id=message_id,
        question=question,
        answer=answer,
        sources=sources,
        questions_remaining=None if quota is None else max(0, quota - used),
    )


@router.get("/conversations")
def my_conversations(user: dict = Depends(get_current_user)):
    return {"conversations": conversations.list_conversations(user["id"])}


@router.get("/conversations/{conv_id}")
def conversation_messages(conv_id: str, user: dict = Depends(get_current_user)):
    conv = conversations.get_conversation(conv_id, user["id"])
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversation introuvable.")
    return {
        "conversation_id": conv_id,
        "title": conv["title"],
        "messages": conversations.get_messages(conv_id),
    }


@router.delete("/conversations/{conv_id}")
def remove_conversation(conv_id: str, user: dict = Depends(get_current_user)):
    if not conversations.delete_conversation(conv_id, user["id"]):
        raise HTTPException(status_code=404, detail="Conversation introuvable.")
    return {"message": "Conversation supprimée", "conversation_id": conv_id}


@router.post("/messages/{message_id}/feedback")
def message_feedback(
    message_id: int, payload: FeedbackRequest, user: dict = Depends(get_current_user)
):
    if payload.rating not in (1, -1):
        raise HTTPException(status_code=400, detail="Le feedback doit être 1 ou -1.")
    if not conversations.set_feedback(message_id, user["id"], payload.rating):
        raise HTTPException(status_code=404, detail="Message introuvable.")
    return {"ok": True}
