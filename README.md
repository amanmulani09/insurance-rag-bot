# Insurance RAG Bot

Insurance RAG Bot is a small retrieval-augmented assistant for an insurance agency website. It ingests a policy or claims knowledge PDF, builds a local FAISS vector index, retrieves relevant passages for a user question, and asks a Groq-hosted LLM to answer using only the retrieved context. The browser UI is a dependency-free Web Component that can be embedded into any static page.

## Product Scope

The system is designed for a focused customer-care workflow:

- Ingest one canonical knowledge PDF into a searchable vector index.
- Answer policy and claims questions from the indexed document.
- Return retrieved source chunks with each answer for transparency.
- Provide a lightweight chat widget that can be dropped into a basic website.

The assistant is intentionally constrained: if the indexed document does not contain the answer, the model is instructed to say so and offer a handoff to a human agent.

## Architecture

```text
frontend/
  index.html               Static demo page
  styles.css               Page-level styles
  chat-widget.js           Native Web Component chat client
  chat-widget.css          Widget styles loaded inside shadow DOM

backend/
  main.py                  FastAPI application composition and lifespan
  app/
    api/                   HTTP routing layer
      api.py               Router aggregator
      routes/chat.py       /ingest and /chat endpoints
    schemas/               Pydantic request/response models
      chat.py
    services/              Application service layer
      rag_service.py       Ingestion, index lifecycle, chat orchestration
    core/                  Configuration and environment loading
      config.py
    rag/                   RAG infrastructure utilities
      pdf_to_text.py       PDF extraction
      chunking.py          Token-based chunking
      embed_store.py       Local embeddings + FAISS persistence
      rag_answer.py        Retrieval + Groq answer generation
```

The backend follows a layered shape:

- API layer validates HTTP input and maps domain errors to HTTP status codes.
- Service layer owns business workflow, in-memory index state, locking, and index preload.
- RAG infrastructure layer handles PDF parsing, chunking, embedding, vector storage, retrieval, and LLM calls.
- Core config centralizes environment-derived settings.

This keeps FastAPI routes thin and makes the RAG workflow testable without binding it directly to HTTP.

## Request Flow

### Ingestion

1. `POST /api/ingest` calls `RagService.ingest()`.
2. The service verifies that `KNOWLEDGE_PDF_PATH` exists.
3. `pdf_to_text()` extracts text from the PDF.
4. `chunk_text()` splits text using token-based chunking.
5. `embed_texts()` embeds chunks locally with SentenceTransformers.
6. FAISS stores normalized vectors in an inner-product index.
7. The FAISS index and chunk metadata are written to disk.
8. The service reloads the saved index into memory.

### Chat

1. `POST /api/chat` validates a non-empty `message`.
2. The service preloads the saved FAISS index if not already in memory.
3. The query is embedded with the same local embedding model used for ingestion.
4. FAISS retrieves the top `RETRIEVAL_K` chunks.
5. Groq generates a grounded answer from the retrieved context.
6. The API returns `{ answer, sources }`.

## API Contract

### `POST /api/ingest`

Builds or rebuilds the local knowledge index.

Response:

```json
{
  "status": "ok",
  "chunks": 12
}
```

Errors:

- `404` if the configured knowledge PDF does not exist.

### `POST /api/chat`

Request:

```json
{
  "message": "What documents do I need for a claim?"
}
```

Response:

```json
{
  "answer": "You need ...",
  "sources": ["Relevant source chunk 1", "Relevant source chunk 2"]
}
```

Errors:

- `422` for empty or invalid input.
- `409` if the knowledge base has not been ingested and no saved index exists.

## Configuration

Backend configuration is read from `backend/.env` and environment variables. Environment variables take precedence.

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant
DATA_DIR=./data
KNOWLEDGE_PDF_PATH=./data/knowledge.pdf
RETRIEVAL_K=4
CHUNK_TOKENS=450
OVERLAP_TOKENS=80
CORS_ORIGINS=*
```

Important defaults:

- Knowledge PDF: `backend/data/knowledge.pdf`
- FAISS index: `backend/data/index.faiss`
- Chunk metadata: `backend/data/chunks.json`
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Chat model: `llama-3.1-8b-instant`

Groq requires `GROQ_API_KEY`. Embeddings are local and do not require a paid embedding API.

## Local Development

### Backend

```bash
cd backend
uv sync
cp .env.example .env
```

Edit `backend/.env` and set `GROQ_API_KEY`.

Place the source PDF at:

```text
backend/data/knowledge.pdf
```

Start the API:

```bash
uv run uvicorn main:app --reload
```

Then ingest the PDF:

```bash
curl -X POST http://localhost:8000/api/ingest
```

Ask a question:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is covered by my policy?"}'
```

### Frontend

```bash
cd frontend
python3 -m http.server 5173
```

Open:

```text
http://localhost:5173
```

The chat widget calls:

```text
http://localhost:8000/api/chat
```

## Technical Decisions

### Local Embeddings

The project uses `sentence-transformers/all-MiniLM-L6-v2` for embeddings. This keeps ingestion and query embedding free of API cost and ensures both document chunks and user queries live in the same vector space.

Vectors are normalized and stored in `faiss.IndexFlatIP`, so inner product behaves like cosine similarity.

### Groq for Answer Generation

Groq is used only for answer generation. The client is created lazily, which avoids failing application import when the API key is missing and avoids unnecessary client creation during retrieval-only tests.

### Index Lifecycle

The service preloads an existing FAISS index on FastAPI startup. If no index exists, `/api/chat` returns `409` until ingestion runs.

Ingestion is guarded by an `RLock` to prevent concurrent requests from rebuilding and replacing the same index files at the same time. Index and metadata writes use temporary files followed by atomic replacement.

### Frontend Web Component

The chat widget is implemented as a native custom element. It uses shadow DOM so widget styles stay isolated from host-page styles. The widget has no build step and can be embedded with:

```html
<script type="module" src="./chat-widget.js"></script>
<chat-widget api-url="http://localhost:8000/api/chat"></chat-widget>
```

## Operational Notes

- The first embedding call may download model weights from Hugging Face and will be slower.
- `backend/data/` should be treated as runtime state, not source code.
- For production, restrict `CORS_ORIGINS` instead of using `*`.
- For multiple API workers, use shared persistent storage and coordinate ingestion externally; in-memory index state is per process.
- For large document collections, replace `IndexFlatIP` with an approximate FAISS index and add document/page metadata.

## Future Improvements

- Add upload-based ingestion instead of a fixed PDF path.
- Store source metadata such as file name, page number, and chunk ID.
- Add streaming chat responses.
- Add an async background ingestion job with progress status.
- Add integration tests for ingestion and retrieval.
- Add rate limiting and request logging.
- Add evaluation fixtures for retrieval quality and grounded-answer behavior.
