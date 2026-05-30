from fastapi import APIRouter, HTTPException, status

from app.schemas.chat import ChatRequest, ChatResponse, IngestResponse
from app.services.rag_service import (
    KnowledgeBaseNotReadyError,
    KnowledgeDocumentNotFoundError,
    rag_service,
)


router = APIRouter(tags=["rag"])


@router.post("/ingest", response_model=IngestResponse)
def ingest():
    try:
        chunk_count = rag_service.ingest()
    except KnowledgeDocumentNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    return IngestResponse(status="ok", chunks=chunk_count)


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest):
    try:
        answer, sources = rag_service.answer(payload.message)
    except KnowledgeBaseNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return ChatResponse(answer=answer, sources=sources)
