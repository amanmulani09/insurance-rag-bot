import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.chat import ChatRequest, ChatResponse, IngestResponse
from app.services.rag_service import (
    KnowledgeBaseNotReadyError,
    KnowledgeDocumentNotFoundError,
    rag_service,
)


router = APIRouter(tags=["rag"])
logger = logging.getLogger(__name__)


@router.post("/ingest", response_model=IngestResponse)
def ingest():
    logger.info("HTTP /ingest requested")
    try:
        chunk_count = rag_service.ingest()
    except KnowledgeDocumentNotFoundError as exc:
        logger.warning("HTTP /ingest failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    logger.info("HTTP /ingest completed: chunks=%s", chunk_count)
    return IngestResponse(status="ok", chunks=chunk_count)


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    logger.info("HTTP /chat requested: message_chars=%s", len(payload.message))
    try:
        answer, sources = rag_service.answer(payload.message)
    except KnowledgeBaseNotReadyError as exc:
        logger.warning("HTTP /chat rejected: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    logger.info(
        "HTTP /chat completed: answer_chars=%s sources=%s",
        len(answer),
        len(sources),
    )
    return ChatResponse(answer=answer, sources=sources)
