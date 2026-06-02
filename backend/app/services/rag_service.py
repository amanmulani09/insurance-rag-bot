import logging
from pathlib import Path
from threading import RLock

from app.core import config
from app.rag.chunking import chunk_text
from app.rag.embed_store import build_and_save_index, load_index
from app.rag.pdf_to_text import pdf_to_text
from app.rag.rag_answer import generate_answer, retrieve

logger = logging.getLogger(__name__)


class KnowledgeBaseNotReadyError(RuntimeError):
    pass


class KnowledgeDocumentNotFoundError(FileNotFoundError):
    pass


class RagService:
    def __init__(
        self,
        pdf_path: Path = config.PDF_PATH,
        index_path: Path = config.INDEX_PATH,
        meta_path: Path = config.META_PATH,
    ):
        self.pdf_path = pdf_path
        self.index_path = index_path
        self.meta_path = meta_path
        self._index = None
        self._chunks: list[str] | None = None
        self._lock = RLock()
        logger.info(
            "RagService initialized: pdf_path=%s index_path=%s meta_path=%s",
            self.pdf_path,
            self.index_path,
            self.meta_path,
        )

    def preload(self) -> None:
        logger.info("Preload requested")
        with self._lock:
            if self._has_saved_index():
                logger.info(
                    "Saved index found; loading index=%s meta=%s",
                    self.index_path,
                    self.meta_path,
                )
                self._index, self._chunks = load_index(
                    str(self.index_path),
                    str(self.meta_path),
                )
                logger.info("Preload complete: chunks=%s", len(self._chunks))
            else:
                logger.info("Preload skipped: saved index files not found")

    def ingest(self) -> int:
        logger.info("Ingestion started: pdf_path=%s", self.pdf_path)
        with self._lock:
            if not self.pdf_path.exists():
                logger.error("Ingestion failed: knowledge PDF missing at %s", self.pdf_path)
                raise KnowledgeDocumentNotFoundError(
                    f"Knowledge PDF not found at {self.pdf_path}"
                )

            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.meta_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(
                "Ingestion paths ready: index_dir=%s meta_dir=%s",
                self.index_path.parent,
                self.meta_path.parent,
            )

            text = pdf_to_text(str(self.pdf_path))
            logger.info("PDF extraction complete: text_chars=%s", len(text))
            chunks = chunk_text(
                text,
                chunk_tokens=config.CHUNK_TOKENS,
                overlap_tokens=config.OVERLAP_TOKENS,
            )
            logger.info("Chunking complete: chunks=%s", len(chunks))
            build_and_save_index(chunks, str(self.index_path), str(self.meta_path))
            logger.info("Index persisted; reloading into memory")
            self._index, self._chunks = load_index(
                str(self.index_path),
                str(self.meta_path),
            )
            logger.info("Ingestion complete: chunks=%s", len(chunks))
            return len(chunks)

    def answer(self, message: str) -> tuple[str, list[str]]:
        logger.info("Answer flow started: message_chars=%s", len(message))
        index, chunks = self._get_index_and_chunks()
        logger.info("Index ready for retrieval: chunks=%s", len(chunks))
        hits = retrieve(message, index, chunks, k=config.RETRIEVAL_K)
        logger.info("Retrieval complete: hits=%s", len(hits))
        answer = generate_answer(message, hits)
        logger.info("Answer generation complete: answer_chars=%s", len(answer))
        return answer, hits

    def _get_index_and_chunks(self):
        with self._lock:
            if self._index is None or self._chunks is None:
                logger.info("In-memory index missing; checking saved index files")
                if not self._has_saved_index():
                    logger.warning("Knowledge base not ready: saved index files missing")
                    raise KnowledgeBaseNotReadyError(
                        "Knowledge base not ingested yet. Call ingest first."
                    )
                logger.info("Loading saved index into memory")
                self._index, self._chunks = load_index(
                    str(self.index_path),
                    str(self.meta_path),
                )
                logger.info("Saved index loaded: chunks=%s", len(self._chunks))
            return self._index, self._chunks

    def _has_saved_index(self) -> bool:
        return self.index_path.exists() and self.meta_path.exists()


rag_service = RagService()
