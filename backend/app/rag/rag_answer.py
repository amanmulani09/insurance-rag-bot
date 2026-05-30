import os
import numpy as np
from app.rag.embed_store import embed_texts

CHAT_MODEL = os.getenv("GROQ_MODEL", os.getenv("CHAT_MODEL", "llama-3.1-8b-instant"))

def embed_query(query: str) -> np.ndarray:
    return embed_texts([query])

def retrieve(query: str, index, chunks: list[str], k: int = 4) -> list[str]:
    qvec = embed_query(query)
    scores, ids = index.search(qvec, k)
    results = []
    for i in ids[0]:
        if i == -1:
            continue
        results.append(chunks[i])
    return results

def generate_answer(user_question: str, retrieved_chunks: list[str]) -> str:
    from groq import Groq

    client = Groq()
    context = "\n\n".join(retrieved_chunks)
    instructions = (
        "You are an Insurance Agency Customer Care assistant. "
        "Use only the provided context to answer. "
        "If the answer is not in the context, say you do not have it in the documents "
        "and offer to connect to a human agent. "
        "Keep it short, friendly, and clear."
    )

    response = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": instructions},
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion:\n{user_question}",
            },
        ],
        temperature=0.2,
        max_completion_tokens=512,
    )
    return response.choices[0].message.content or ""
