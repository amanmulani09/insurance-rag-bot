from pathlib import Path
from threading import RLock

from app.core import config
from app.rag.chunking import chunk_text
from app.rag.embed_store import build_and_save_index, load_index
from app.rag.pdf_to_text import pdf_to_text
from app.rag.rag_answer import generate_answer, retrieve


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

    def preload(self) -> None:
        with self._lock:
            if self._has_saved_index():
                self._index, self._chunks = load_index(
                    str(self.index_path),
                    str(self.meta_path),
                )

    def ingest(self) -> int:
        with self._lock:
            if not self.pdf_path.exists():
                raise KnowledgeDocumentNotFoundError(
                    f"Knowledge PDF not found at {self.pdf_path}"
                )

            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.meta_path.parent.mkdir(parents=True, exist_ok=True)

            text = pdf_to_text(str(self.pdf_path))
            chunks = chunk_text(
                text,
                chunk_tokens=config.CHUNK_TOKENS,
                overlap_tokens=config.OVERLAP_TOKENS,
            )
            build_and_save_index(chunks, str(self.index_path), str(self.meta_path))
            self._index, self._chunks = load_index(
                str(self.index_path),
                str(self.meta_path),
            )
            return len(chunks)

    def answer(self, message: str) -> tuple[str, list[str]]:
        index, chunks = self._get_index_and_chunks()
        hits = retrieve(message, index, chunks, k=config.RETRIEVAL_K)
        answer = generate_answer(message, hits)
        return answer, hits

    def _get_index_and_chunks(self):
        with self._lock:
            if self._index is None or self._chunks is None:
                if not self._has_saved_index():
                    raise KnowledgeBaseNotReadyError(
                        "Knowledge base not ingested yet. Call ingest first."
                    )
                self._index, self._chunks = load_index(
                    str(self.index_path),
                    str(self.meta_path),
                )
            return self._index, self._chunks

    def _has_saved_index(self) -> bool:
        return self.index_path.exists() and self.meta_path.exists()


rag_service = RagService()
