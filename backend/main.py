from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.api import router as api_router
from app.services.rag_service import rag_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    rag_service.preload()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(api_router, prefix="/api")
