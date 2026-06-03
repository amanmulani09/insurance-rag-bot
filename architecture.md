**Big Picture**

This app is an insurance customer-care RAG chatbot.

RAG means Retrieval-Augmented Generation. Instead of asking the LLM to answer from memory, the app first retrieves relevant chunks from your insurance knowledge PDF, then sends only those chunks to Groq so the answer is grounded in your document.

The project has two parts:

```text
backend/   FastAPI + RAG pip**Big Picture**

This app is an insurance customer-care RAG chatbot.

RAG means Retrieval-Augmented Generation. Instead of asking the LLM to answer from memory, the app first retrieves relevant chunks from your insurance knowledge PDF, then sends only those chunks to Groq so the answer is grounded in your document.

The project has two parts:

```text
backend/   FastAPI + RAG pipeline
frontend/  Plain HTML/CSS/JS chat widget
```

**Backend Architecture**

The backend follows a layered architecture:

```text
backend/
  main.py
  app/
    core/
    api/
    schemas/
    services/
    rag/
```

Each layer has a specific responsibility.

**1. `main.py`**

[main.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/main.py) creates the FastAPI app.

It does three important things:

```python
configure_logging()
```

Sets up backend logs.

```python
rag_service.preload()
```

On startup, tries to load an existing FAISS index from disk.

```python
app.include_router(api_router, prefix="/api")
```

Mounts all API routes under `/api`.

So your endpoints become:

```text
POST /api/ingest
POST /api/chat
```

**2. `app/core/`**

This is shared app configuration.

[config.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/core/config.py) reads `.env` and defines values like:

```text
GROQ_API_KEY
GROQ_MODEL
DATA_DIR
KNOWLEDGE_PDF_PATH
RETRIEVAL_K
CHUNK_TOKENS
OVERLAP_TOKENS
LOG_LEVEL
```

[logging.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/core/logging.py) configures standard Python logging so you can see each step of the flow.

**3. `app/api/`**

This is the HTTP layer.

[chat.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/api/routes/chat.py) exposes:

```text
POST /api/ingest
POST /api/chat
```

It does not contain RAG logic. It only:

- Receives requests
- Calls the service layer
- Converts service errors into HTTP errors
- Returns response models

Example:

```python
answer, sources = rag_service.answer(payload.message)
```

**4. `app/schemas/`**

This layer defines request and response shapes with Pydantic.

[schemas/chat.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/schemas/chat.py) defines:

```python
ChatRequest
ChatResponse
IngestResponse
```

For example, `/api/chat` expects:

```json
{
  "message": "How do I file a claim?"
}
```

And returns:

```json
{
  "answer": "...",
  "sources": ["..."]
}
```

**5. `app/services/`**

This is the orchestration/business layer.

[rag_service.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/services/rag_service.py) owns the main application workflow.

It keeps:

```python
self._index
self._chunks
self._lock
```

That means it stores the loaded FAISS index and chunks in memory so every chat request does not have to reload them from disk.

It has three important methods:

```python
preload()
```

Loads existing `index.faiss` and `chunks.json` on startup if they exist.

```python
ingest()
```

Reads the PDF, chunks it, embeds it, builds FAISS index, saves it, and loads it into memory.

```python
answer(message)
```

Retrieves relevant chunks and generates an answer.

This layer is important because it keeps your API routes clean.

**6. `app/rag/`**

This is the RAG infrastructure layer.

It contains the low-level building blocks.

[pdf_to_text.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/rag/pdf_to_text.py)

Reads the PDF:

```python
PdfReader(pdf_path)
```

Extracts text from each page.

[chunking.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/rag/chunking.py)

Splits the extracted text into token chunks.

Default:

```text
450 tokens per chunk
80 token overlap
```

Overlap helps preserve context between chunks.

[embed_store.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/rag/embed_store.py)

Uses local open-source embeddings:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Then stores vectors in FAISS:

```python
faiss.IndexFlatIP(dim)
```

Because vectors are normalized, inner product behaves like cosine similarity.

It writes:

```text
backend/data/index.faiss
backend/data/chunks.json
```

[rag_answer.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/rag/rag_answer.py)

Handles:

- Query embedding
- FAISS search
- Groq answer generation

Flow:

```python
embed_query()
retrieve()
generate_answer()
```

Groq receives only:

```text
retrieved context + user question
```

**Ingestion Flow**

When you call:

```bash
curl -X POST http://localhost:8000/api/ingest
```

The flow is:

```text
/api/ingest
  -> rag_service.ingest()
    -> pdf_to_text()
    -> chunk_text()
    -> build_and_save_index()
      -> embed_texts()
      -> FAISS index.add()
      -> save index.faiss
      -> save chunks.json
    -> load_index()
```

End result:

```text
backend/data/index.faiss
backend/data/chunks.json
```

Also, the index is now loaded into memory.

**Chat Flow**

When the frontend sends:

```json
{
  "message": "How do I file a claim?"
}
```

The flow is:

```text
/api/chat
  -> rag_service.answer(message)
    -> _get_index_and_chunks()
    -> retrieve()
      -> embed_query()
      -> FAISS search
      -> return top chunks
    -> generate_answer()
      -> Groq chat completion
    -> return answer + sources
```

Response:

```json
{
  "answer": "You can file a claim online...",
  "sources": ["Q: How do I file an insurance claim?..."]
}
```

**Frontend Architecture**

The frontend is dependency-free.

```text
frontend/
  index.html
  styles.css
  chat-widget.js
  chat-widget.css
```

[chat-widget.js](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/frontend/chat-widget.js) defines a native Web Component:

```html
<chat-widget api-url="http://localhost:8000/api/chat"></chat-widget>
```

It handles:

- Opening/closing chat modal
- Storing messages in local component state
- Sending user message to backend
- Rendering bot response

It uses Shadow DOM, so the widget CSS does not leak into the page and page CSS does not break the widget.

**Important Runtime Files**

After ingestion, these files matter:

```text
backend/data/knowledge.pdf
backend/data/index.faiss
backend/data/chunks.json
```

`knowledge.pdf` is the source document.

`index.faiss` stores vector embeddings.

`chunks.json` stores the original text chunks.

FAISS only knows vectors, so `chunks.json` is needed to map vector search results back to readable text.

**Why Logging Matters**

You added logs so the flow is visible.

A chat request now shows steps like:

```text
HTTP /chat requested
Answer flow started
Loading saved index
Retrieval started
Query embedding started
FAISS search complete
Answer generation started
Calling Groq chat completions
Groq answer received
HTTP /chat completed
```

That helps debug:

- Whether the index loaded
- Whether retrieval found chunks
- Whether embeddings are running
- Whether Groq is being called
- Where latency happens

**Mental Model**

Think of the app like this:

```text
PDF
 ↓
Text extraction
 ↓
Chunking
 ↓
Local embeddings
 ↓
FAISS vector index
 ↓
User question
 ↓
Query embedding
 ↓
Retrieve relevant chunks
 ↓
Groq LLM
 ↓
Grounded answer
```

The LLM is not searching the PDF directly. FAISS searches the PDF chunks first, then Groq writes the answer using those chunks.eline
frontend/  Plain HTML/CSS/JS chat widget
```

**Backend Architecture**

The backend follows a layered architecture:

```text
backend/
  main.py
  app/
    core/
    api/
    schemas/
    services/
    rag/
```

Each layer has a specific responsibility.

**1. `main.py`**

[main.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/main.py) creates the FastAPI app.

It does three important things:

```python
configure_logging()
```

Sets up backend logs.

```python
rag_service.preload()
```

On startup, tries to load an existing FAISS index from disk.

```python
app.include_router(api_router, prefix="/api")
```

Mounts all API routes under `/api`.

So your endpoints become:

```text
POST /api/ingest
POST /api/chat
```

**2. `app/core/`**

This is shared app configuration.

[config.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/core/config.py) reads `.env` and defines values like:

```text
GROQ_API_KEY
GROQ_MODEL
DATA_DIR
KNOWLEDGE_PDF_PATH
RETRIEVAL_K
CHUNK_TOKENS
OVERLAP_TOKENS
LOG_LEVEL
```

[logging.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/core/logging.py) configures standard Python logging so you can see each step of the flow.

**3. `app/api/`**

This is the HTTP layer.

[chat.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/api/routes/chat.py) exposes:

```text
POST /api/ingest
POST /api/chat
```

It does not contain RAG logic. It only:

- Receives requests
- Calls the service layer
- Converts service errors into HTTP errors
- Returns response models

Example:

```python
answer, sources = rag_service.answer(payload.message)
```

**4. `app/schemas/`**

This layer defines request and response shapes with Pydantic.

[schemas/chat.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/schemas/chat.py) defines:

```python
ChatRequest
ChatResponse
IngestResponse
```

For example, `/api/chat` expects:

```json
{
  "message": "How do I file a claim?"
}
```

And returns:

```json
{
  "answer": "...",
  "sources": ["..."]
}
```

**5. `app/services/`**

This is the orchestration/business layer.

[rag_service.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/services/rag_service.py) owns the main application workflow.

It keeps:

```python
self._index
self._chunks
self._lock
```

That means it stores the loaded FAISS index and chunks in memory so every chat request does not have to reload them from disk.

It has three important methods:

```python
preload()
```

Loads existing `index.faiss` and `chunks.json` on startup if they exist.

```python
ingest()
```

Reads the PDF, chunks it, embeds it, builds FAISS index, saves it, and loads it into memory.

```python
answer(message)
```

Retrieves relevant chunks and generates an answer.

This layer is important because it keeps your API routes clean.

**6. `app/rag/`**

This is the RAG infrastructure layer.

It contains the low-level building blocks.

[pdf_to_text.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/rag/pdf_to_text.py)

Reads the PDF:

```python
PdfReader(pdf_path)
```

Extracts text from each page.

[chunking.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/rag/chunking.py)

Splits the extracted text into token chunks.

Default:

```text
450 tokens per chunk
80 token overlap
```

Overlap helps preserve context between chunks.

[embed_store.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/rag/embed_store.py)

Uses local open-source embeddings:

```text
sentence-transformers/all-MiniLM-L6-v2
```

Then stores vectors in FAISS:

```python
faiss.IndexFlatIP(dim)
```

Because vectors are normalized, inner product behaves like cosine similarity.

It writes:

```text
backend/data/index.faiss
backend/data/chunks.json
```

[rag_answer.py](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/backend/app/rag/rag_answer.py)

Handles:

- Query embedding
- FAISS search
- Groq answer generation

Flow:

```python
embed_query()
retrieve()
generate_answer()
```

Groq receives only:

```text
retrieved context + user question
```

**Ingestion Flow**

When you call:

```bash
curl -X POST http://localhost:8000/api/ingest
```

The flow is:

```text
/api/ingest
  -> rag_service.ingest()
    -> pdf_to_text()
    -> chunk_text()
    -> build_and_save_index()
      -> embed_texts()
      -> FAISS index.add()
      -> save index.faiss
      -> save chunks.json
    -> load_index()
```

End result:

```text
backend/data/index.faiss
backend/data/chunks.json
```

Also, the index is now loaded into memory.

**Chat Flow**

When the frontend sends:

```json
{
  "message": "How do I file a claim?"
}
```

The flow is:

```text
/api/chat
  -> rag_service.answer(message)
    -> _get_index_and_chunks()
    -> retrieve()
      -> embed_query()
      -> FAISS search
      -> return top chunks
    -> generate_answer()
      -> Groq chat completion
    -> return answer + sources
```

Response:

```json
{
  "answer": "You can file a claim online...",
  "sources": ["Q: How do I file an insurance claim?..."]
}
```

**Frontend Architecture**

The frontend is dependency-free.

```text
frontend/
  index.html
  styles.css
  chat-widget.js
  chat-widget.css
```

[chat-widget.js](/Users/amanmulani/ai-engineering/rag/insurance-rag-bot/frontend/chat-widget.js) defines a native Web Component:

```html
<chat-widget api-url="http://localhost:8000/api/chat"></chat-widget>
```

It handles:

- Opening/closing chat modal
- Storing messages in local component state
- Sending user message to backend
- Rendering bot response

It uses Shadow DOM, so the widget CSS does not leak into the page and page CSS does not break the widget.

**Important Runtime Files**

After ingestion, these files matter:

```text
backend/data/knowledge.pdf
backend/data/index.faiss
backend/data/chunks.json
```

`knowledge.pdf` is the source document.

`index.faiss` stores vector embeddings.

`chunks.json` stores the original text chunks.

FAISS only knows vectors, so `chunks.json` is needed to map vector search results back to readable text.

**Why Logging Matters**

You added logs so the flow is visible.

A chat request now shows steps like:

```text
HTTP /chat requested
Answer flow started
Loading saved index
Retrieval started
Query embedding started
FAISS search complete
Answer generation started
Calling Groq chat completions
Groq answer received
HTTP /chat completed
```

That helps debug:

- Whether the index loaded
- Whether retrieval found chunks
- Whether embeddings are running
- Whether Groq is being called
- Where latency happens

**Mental Model**

Think of the app like this:

```text
PDF
 ↓
Text extraction
 ↓
Chunking
 ↓
Local embeddings
 ↓
FAISS vector index
 ↓
User question
 ↓
Query embedding
 ↓
Retrieve relevant chunks
 ↓
Groq LLM
 ↓
Grounded answer
```

The LLM is not searching the PDF directly. FAISS searches the PDF chunks first, then Groq writes the answer using those chunks.
