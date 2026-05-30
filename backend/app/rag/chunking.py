import tiktoken
from typing import List

def chunk_text(text: str, chunk_tokens: int = 450, overlap_tokens: int = 80) -> List[str]:
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