import os
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = BACKEND_DIR / "data"
DEFAULT_ENV_PATH = BACKEND_DIR / ".env"


def load_env_file(path: Path = DEFAULT_ENV_PATH) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_env_file()

def backend_path(value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return BACKEND_DIR / path


DATA_DIR = backend_path(os.getenv("DATA_DIR", DEFAULT_DATA_DIR))
PDF_PATH = backend_path(os.getenv("KNOWLEDGE_PDF_PATH", DATA_DIR / "knowledge.pdf"))
INDEX_PATH = backend_path(os.getenv("FAISS_INDEX_PATH", DATA_DIR / "index.faiss"))
META_PATH = backend_path(os.getenv("CHUNKS_META_PATH", DATA_DIR / "chunks.json"))

CHAT_MODEL = os.getenv("GROQ_MODEL", os.getenv("CHAT_MODEL", "llama-3.1-8b-instant"))
RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", "4"))
CHUNK_TOKENS = int(os.getenv("CHUNK_TOKENS", "450"))
OVERLAP_TOKENS = int(os.getenv("OVERLAP_TOKENS", "80"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]
