import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from agents.query_planner import QueryPlanner
from backend.core.logging import get_logger
from backend.models.chat import ChatMessage
from generation.answer_generator import AnswerGenerator
from generation.citation_builder import CitationBuilder
from generation.response_cache import ResponseCache

logger = get_logger(__name__)


class QueryService:

    def __init__(self):
        self.planner = QueryPlanner()
        self.generator = AnswerGenerator()
        self.citation_builder = CitationBuilder()
        self.cache = ResponseCache()

    async def answer_query(
        self,
        db: AsyncSession,
        query: str,
        document_ids: list[str] | None = None,
        session_id: str | None = None,
        top_k: int = 8,
        user_id: str | None = None,
    ) -> dict:
        session_id = session_id or str(uuid.uuid4())

        cached = self.cache.get(query, document_ids)
        if cached:
            cached["session_id"] = session_id
            if user_id:
                await self.link_session_to_user(db, user_id, session_id, title=query[:50])
            return cached

        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=query,
        )
        db.add(user_message)
        await db.flush()

        plan_result = await self.planner.plan_and_execute(
            query=query,
            document_ids=document_ids,
            db=db,
        )

        evidence = plan_result["evidence"]
        context_chunks = evidence["all_chunks"][:top_k]

        generation_result = self.generator.generate(query, context_chunks)
        citations = self.citation_builder.build_citations(context_chunks)

        response = {
            "answer": generation_result["answer"],
            "session_id": session_id,
            "citations": citations,
            "llm_provider": generation_result["provider"],
            "llm_model": generation_result["model"],
            "chunks_retrieved": len(evidence["all_chunks"]),
            "chunks_after_rerank": len(context_chunks),
            "tools_used": plan_result["tools_used"],
        }

        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=generation_result["answer"],
            document_ids=",".join(document_ids) if document_ids else None,
            citations=json.dumps(citations) if citations else None,
            chunks_retrieved=len(evidence["all_chunks"]),
            chunks_after_rerank=len(context_chunks),
            llm_provider=generation_result["provider"],
            llm_model=generation_result["model"],
        )
        db.add(assistant_message)
        await db.flush()

        if user_id:
            await self.link_session_to_user(db, user_id, session_id, title=query[:50])

        self.cache.set(query, document_ids, response)

        logger.info("Query answered", session_id=session_id, query=query[:50])

        return response

    async def link_session_to_user(
        self, db: AsyncSession, user_id: str, session_id: str, title: str | None = None
    ) -> None:
        from sqlalchemy import select

        from backend.models.user_session import UserSession

        result = await db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id, UserSession.session_id == session_id
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            existing.title = existing.title or title
            await db.flush()
            return

        session_row = UserSession(user_id=user_id, session_id=session_id, title=title)
        db.add(session_row)
        await db.flush()

    async def list_sessions_for_user(self, db: AsyncSession, user_id: str) -> list:
        from sqlalchemy import select

        from backend.models.user_session import UserSession

        result = await db.execute(
            select(UserSession)
            .where(UserSession.user_id == user_id)
            .order_by(UserSession.updated_at.desc())
        )
        return list(result.scalars().all())

    async def user_owns_session(self, db: AsyncSession, user_id: str, session_id: str) -> bool:
        from sqlalchemy import select

        from backend.models.user_session import UserSession

        result = await db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id, UserSession.session_id == session_id
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_session_messages(self, db: AsyncSession, session_id: str) -> list[ChatMessage]:
        from sqlalchemy import select

        result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(result.scalars().all())
