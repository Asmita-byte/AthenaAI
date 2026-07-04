import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from generation.answer_generator import AnswerGenerator

from backend.api.deps import get_current_user
from backend.core.exceptions import BaseAppException
from backend.core.logging import get_logger
from backend.dependencies import DatabaseDep
from backend.models.user import User
from backend.schemas.query import QueryRequest, QueryResponse
from backend.services.query_service import QueryService

logger = get_logger(__name__)
router = APIRouter(prefix="/query", tags=["Query"])

query_service = QueryService()


@router.post("")
async def query_documents(
    request: QueryRequest,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
):
    try:
        result = await query_service.answer_query(
            db=db,
            query=request.query,
            document_ids=request.document_ids,
            session_id=request.session_id,
            top_k=request.top_k,
            user_id=current_user.id,
        )
        return result

    except BaseAppException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error_code": e.error_code, "message": e.message},
        )


@router.post("/chat")
async def normal_chat(
    request: QueryRequest,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
):
    try:
        from groq import Groq
        from backend.config import get_settings
        from backend.models.chat import ChatMessage

        settings = get_settings()
        session_id = request.session_id or __import__("uuid").uuid4().hex

        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=request.query,
        )
        db.add(user_message)
        await db.flush()

        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are Athena AI, a helpful and friendly assistant. Answer conversationally from your general knowledge."
                },
                {
                    "role": "user",
                    "content": request.query
                }
            ],
            temperature=0.7,
            max_tokens=1024,
        )

        answer = response.choices[0].message.content

        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=answer,
            llm_provider="groq",
            llm_model=settings.groq_model,
        )
        db.add(assistant_message)
        await db.flush()

        await query_service.link_session_to_user(
            db, current_user.id, session_id, title=request.query[:50]
        )

        return {
            "answer": answer,
            "session_id": session_id,
            "citations": [],
            "llm_provider": "groq",
            "llm_model": settings.groq_model,
            "chunks_retrieved": 0,
            "chunks_after_rerank": 0,
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error_code": "LLM_ERROR", "message": str(e)},
        )


@router.get("/history/sessions")
async def list_my_sessions(
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
):
    sessions = await query_service.list_sessions_for_user(db, current_user.id)
    return [
        {
            "session_id": s.session_id,
            "title": s.title,
            "created_at": s.created_at,
            "updated_at": s.updated_at,
        }
        for s in sessions
    ]


@router.get("/history/{session_id}")
async def get_query_history(
    session_id: str,
    db: DatabaseDep,
    current_user: User = Depends(get_current_user),
):
    owns = await query_service.user_owns_session(db, current_user.id, session_id)
    if not owns:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    messages = await query_service.get_session_messages(db, session_id)
    return [
        {
            "role": m.role,
            "content": m.content,
            "citations": json.loads(m.citations) if m.citations else [],
            "created_at": m.created_at,
        }
        for m in messages
    ]