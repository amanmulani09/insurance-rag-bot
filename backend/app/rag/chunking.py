import tiktoken
from typing import List

def chunk_text(text: str, chunk_tokens: int = 450, overlap_tokens: int = 80) -> List[str]:
    if chunk_tokens <= 0:
        raise ValueError("chunk_tokens must be greater than 0")
    if overlap_tokens < 0:
        raise ValueError("overlap_tokens must be greater than or equal to 0")
    if overlap_tokens >= chunk_tokens:
        raise ValueError("overlap_tokens must be less than chunk_tokens")

    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)

    chunks = []
    start = 0
    while start < len(tokens):
        end = start + chunk_tokens
        chunk = enc.decode(tokens[start:end])
        chunks.append(chunk)
        start = end - overlap_tokens
        if start < 0:
            start = 0
    return chunks
