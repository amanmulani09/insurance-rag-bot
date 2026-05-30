import json
import os
from pathlib import Path
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model

def embed_texts(texts: list[str]) -> np.ndarray:
    arr = get_embedding_model().encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).astype("float32")
    faiss.normalize_L2(arr)
    return arr

def build_and_save_index(chunks: list[str], index_path: str, meta_path: str):
    index_file = Path(index_path)
    meta_file = Path(meta_path)
    index_file.parent.mkdir(parents=True, exist_ok=True)
    meta_file.parent.mkdir(parents=True, exist_ok=True)

    vectors = embed_texts(chunks)
    dim = vectors.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(vectors)

    tmp_index_path = index_file.with_suffix(index_file.suffix + ".tmp")
    tmp_meta_path = meta_file.with_suffix(meta_file.suffix + ".tmp")

    faiss.write_index(index, str(tmp_index_path))
    with open(tmp_meta_path, "w", encoding="utf-8") as f:
        json.dump({"chunks": chunks}, f, ensure_ascii=False, indent=2)
    os.replace(tmp_index_path, index_file)
    os.replace(tmp_meta_path, meta_file)

def load_index(index_path: str, meta_path: str):
    index = faiss.read_index(index_path)
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    return index, meta["chunks"]
