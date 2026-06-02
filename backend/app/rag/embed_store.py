import json
import logging
import os
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
logger = logging.getLogger(__name__)

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading embedding model: model=%s", EMBED_MODEL)
        _model = SentenceTransformer(EMBED_MODEL)
        logger.info("Embedding model loaded")
    return _model

def embed_texts(texts: list[str]) -> np.ndarray:
    logger.info("Embedding started: texts=%s", len(texts))
    arr = get_embedding_model().encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")
    faiss.normalize_L2(arr)
    logger.info("Embedding complete: shape=%s dtype=%s", arr.shape, arr.dtype)
    return arr

def build_and_save_index(chunks: list[str], index_path: str, meta_path: str):
    index_file = Path(index_path)
    meta_file = Path(meta_path)
    index_file.parent.mkdir(parents=True, exist_ok=True)
    meta_file.parent.mkdir(parents=True, exist_ok=True)
    logger.info(
        "Index build started: chunks=%s index_path=%s meta_path=%s",
        len(chunks),
        index_file,
        meta_file,
    )

    vectors = embed_texts(chunks)
    dim = vectors.shape[1]
    logger.info("Creating FAISS index: dim=%s", dim)
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)
    logger.info("FAISS vectors added: ntotal=%s", index.ntotal)

    tmp_index_path = index_file.with_suffix(index_file.suffix + ".tmp")
    tmp_meta_path = meta_file.with_suffix(meta_file.suffix + ".tmp")

    logger.info("Writing FAISS index: tmp_path=%s", tmp_index_path)
    faiss.write_index(index, str(tmp_index_path))
    logger.info("Writing chunk metadata: tmp_path=%s", tmp_meta_path)
    with open(tmp_meta_path, "w", encoding="utf-8") as f:
        json.dump({"chunks": chunks}, f, ensure_ascii=False, indent=2)
    os.replace(tmp_index_path, index_file)
    os.replace(tmp_meta_path, meta_file)
    logger.info("Index build persisted: index_path=%s meta_path=%s", index_file, meta_file)

def load_index(index_path: str, meta_path: str):
    logger.info("Loading FAISS index: index_path=%s meta_path=%s", index_path, meta_path)
    index = faiss.read_index(index_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    logger.info("FAISS index loaded: ntotal=%s chunks=%s", index.ntotal, len(meta["chunks"]))
    return index, meta["chunks"]
