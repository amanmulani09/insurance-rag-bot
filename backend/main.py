from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.api import router as api_router
from app.core.config import CORS_ORIGINS
from app.core.logging import configure_logging
from app.services.rag_service import rag_service

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    import logging

    logger = logging.getLogger(__name__)
    logger.info("Application startup: preloading RAG index if available")
    rag_service.preload()
    logger.info("Application startup complete")
    yield
    logger.info("Application shutdown")


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(api_router, prefix="/api")
