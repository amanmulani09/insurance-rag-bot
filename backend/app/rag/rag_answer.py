import logging

import numpy as np
from groq import Groq

from app.core.config import CHAT_MODEL
from app.rag.embed_store import embed_texts

_client: Groq | None = None
logger = logging.getLogger(__name__)


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        logger.info("Creating Groq client")
        _client = Groq()
        logger.info("Groq client ready")
    return _client

def embed_query(query: str) -> np.ndarray:
    logger.info("Query embedding started: query_chars=%s", len(query))
    return embed_texts([query])

def retrieve(query: str, index, chunks: list[str], k: int = 4) -> list[str]:
    logger.info("Retrieval started: k=%s chunks=%s", k, len(chunks))
    qvec = embed_query(query)
    scores, ids = index.search(qvec, k)
    logger.info(
        "FAISS search complete: ids=%s scores=%s",
        ids[0].tolist(),
        [round(float(score), 4) for score in scores[0]],
    )
    results = []
    for i in ids[0]:
        if i == -1:
            continue
        results.append(chunks[i])
    logger.info("Retrieval results assembled: hits=%s", len(results))
    return results

def generate_answer(user_question: str, retrieved_chunks: list[str]) -> str:

    logger.info(
        "Answer generation started: model=%s question_chars=%s chunks=%s",
        CHAT_MODEL,
        len(user_question),
        len(retrieved_chunks),
    )
    client = get_groq_client()
    context = "\n\n".join(retrieved_chunks)
    logger.info("Answer context prepared: context_chars=%s", len(context))
    instructions = (
        "You are an Insurance Agency Customer Care assistant. "
        "Use only the provided context to answer. "
        "If the answer is not in the context, say you do not have it in the documents "
        "and offer to connect to a human agent. "
        "Keep it short, friendly, and clear."
    )

    logger.info("Calling Groq chat completions")
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
    answer = response.choices[0].message.content or ""
    logger.info("Groq answer received: answer_chars=%s", len(answer))
    return answer
