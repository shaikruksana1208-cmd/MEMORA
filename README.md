# 🧠 MEMORA

### Learn it. Understand it. Remember it.

MEMORA is an AI-powered personalized learning and memory platform designed to help students understand difficult topics, revise faster, plan their studies, and learn from their own study materials.

## 🌐 Live Demo

https://memora-learning-ai.onrender.com

## 📌 Problem

Students often use different applications for different study needs:

- Understanding difficult concepts
- Summarizing notes
- Preparing for quizzes
- Planning study time
- Revising before exams
- Learning from PDFs and presentations

Switching between different tools can make studying less organized and time-consuming.

## 💡 Solution

MEMORA brings these learning activities together in one student-focused platform.

Students can enter a topic or provide study material, and MEMORA uses AI to generate useful learning content in a simple and understandable format.

## ✨ Features

### 🧠 AI Study Tools

- Explain difficult topics simply
- Summarize study content
- Generate quizzes
- Improve written answers
- Explain concepts in an easier way
- Help students when they don't understand a topic

### ⚡ Quick Study

Students can enter a topic and choose a short study duration.

MEMORA creates a focused mini learning session containing:

- Core concept
- Important points
- Simple example
- Quick practice
- Memory trick
- Final recap

### 📅 Study Planner

Students can enter:

- Exam name
- Exam date
- Subjects
- Available study hours

MEMORA generates a structured study plan with specific study topics and activities.

### 🍅 Pomodoro Focus Mode

A built-in study timer helps students organize focused study sessions and breaks.

Available modes include:

- 25 / 5
- 50 / 10
- 15 / 5

### 📎 Upload & Study

Students can upload study material including:

- PDF
- TXT
- Markdown (`.md`)
- PPT
- PPTX
- JPG
- JPEG
- PNG
- WEBP

The uploaded content can then be used for learning activities such as:

- Summarization
- Simple explanations
- Important points
- Quiz generation

## 🤖 AI Integration

MEMORA uses the Gemini API to generate personalized learning content.

The application uses structured prompts instead of treating the AI as a generic chatbot.

Different learning tasks use different instructions so that the generated response is appropriate for the student's goal.

Examples include:

- Explanation prompts
- Summary prompts
- Quiz prompts
- Study-planning prompts
- Quick-study prompts
- Learning-material prompts

## 🛠️ Technology Stack

### Unified public application

- HTML
- CSS
- JavaScript
- FastAPI is the public ASGI host.
- The existing Flask application is mounted behind FastAPI for Level 1 and Level 2 routes and assets.
- Existing Beginner and Intermediate functionality remains in Flask.

### Advanced document tutor

- FastAPI API in `fastapi_app.py`
- Streamlit client in `streamlit_app.py`
- Pydantic request schemas in `api_schemas.py`
- LangGraph workflow in `rag/workflow.py`
- FAISS vector retrieval

### AI and document processing

- Google Gemini API
- PyPDF for PDF text extraction
- UTF-8 text extraction for TXT and Markdown
- NumPy and FAISS for vector indexing and retrieval

### Container

- Docker with a Python 3.11 slim image

## Advanced Architecture

The Advanced Document Tutor keeps ingestion and question answering separate. Uploaded document text becomes a FAISS index; each question is refined and used to retrieve and rerank relevant chunks before Gemini generates an answer grounded in that evidence.

```text
Upload
   -> Extract text and retain filename/page metadata
   -> Chunk
   -> Embed chunks
   -> Build FAISS index
   -> Refine question
   -> Embed refined query and retrieve FAISS candidates
   -> Rerank candidates locally
   -> Build grounded prompt from selected chunks
   -> Generate answer with Gemini
   -> Check answer against retrieved evidence
   -> Assemble source filename/page citations
   -> Return answer and sources
```

### Ingestion and retrieval

- Supported Document Tutor formats are PDF, TXT, and Markdown (`.md`).
- PDF pages are extracted with `pypdf`; TXT and Markdown are read as UTF-8 single-page documents. Empty, unreadable, unsupported, and scanned PDFs without extractable text are rejected with clear errors.
- `rag/chunker.py` creates overlapping chunks while retaining filenames and page numbers.
- `rag/embeddings.py` creates Gemini embeddings on the server. `rag/vector_store.py` builds a FAISS index and retrieves an initial candidate pool.
- `rag/query_refiner.py` deterministically simplifies common conversational phrasing before query embedding. If refinement fails, the original question is used.
- `rag/reranker.py` locally reranks FAISS candidates using normalized retrieval rank and query-token coverage; FAISS results are the initial candidates and remain the fallback order if reranking fails.
- `rag/generator.py` builds the answer prompt from the original user question and retrieved evidence. `rag/groundedness.py` applies a deterministic evidence-overlap safeguard; this is a heuristic, not a proof of semantic entailment.
- Answers include source filename and page information from the selected chunks.

### LangGraph and schemas

`rag/workflow.py` orchestrates query refinement, retrieval, reranking, prompt construction, generation, groundedness checking, and source assembly. It reuses the existing RAG modules rather than reimplementing them in API handlers.

`api_schemas.py` defines Pydantic v2 request schemas. FastAPI validates document questions, reports clear HTTP errors, and preserves the `{success, answer, sources}` success response structure.

## One Public MEMORA URL

The unified deployment presents one MEMORA landing page with three levels:

- **Level 1 → Beginner:** AI study utilities, planning, focus tools, and study-material helpers.
- **Level 2 → Intermediate RAG:** the existing Flask Document Tutor for supported document uploads and source-based answers.
- **Level 3 → Advanced RAG:** the Advanced Assistant with query refinement, retrieval, reranking, grounded generation, groundedness checks, and sources.

FastAPI is the public host. It serves its own health endpoints and Advanced routes, then mounts the unchanged Flask app through `a2wsgi` as the fallback for existing Level 1 and Level 2 routes, HTML, JavaScript, and CSS. The landing page links to all three levels; Level 3 is a same-origin FastAPI-served page.

## FastAPI Endpoints

The Advanced API uses a separate path prefix to avoid collisions with Flask's existing Level 2 routes. Flask keeps its existing `/api/index-document` and `/api/document-question` endpoints.

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness check; preserves the existing `{status, service}` response. |
| `GET` | `/ready` | Local readiness check; verifies that the Gemini client is configured without making a Gemini request. |
| `POST` | `/api/advanced/index-document` | Multipart upload using the `file` field; indexes PDF, TXT, or Markdown and returns filename, page count, and chunk count. |
| `POST` | `/api/advanced/document-question` | JSON body `{"question": "..."}`; returns `{success, answer, sources}`. |

Upload requests are limited to 25 MiB. Invalid/empty files, missing indexed documents, invalid questions, embedding/retrieval failures, and provider overloads receive HTTP errors without exposing stack traces or secrets in responses.

## Streamlit UI

`streamlit_app.py` is a thin client for the FastAPI endpoints; it does not implement RAG itself. It supports PDF/TXT/Markdown upload, indexing status, question submission, answers, source filename/page display, connection status, and validation messages.

The UI shows spinner/loading feedback during indexing and question answering. HTTP requests have bounded connect/read timeouts. Token streaming is not implemented: the current Gemini helper and LangGraph workflow return a complete answer string, and converting them to token streaming would change the generation path. The existing endpoint and reliable loading feedback are retained instead.

## Configuration and Local Run

Use Python 3.11 or newer. From the repository root, create and activate a virtual environment, then install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The Gemini API key is read by the server from `GEMINI_API_KEY`. For local development, set it in the process environment or use a local `.env` file in the repository root. The `.env` file is excluded from Git and Docker build contexts; do not commit it or put a real key in source files, README examples, or container images.

Start the unified FastAPI backend from the repository root with one worker (the document index is process-local):

```powershell
python -m uvicorn fastapi_app:app --host 127.0.0.1 --port 8000 --workers 1
```

Open `http://127.0.0.1:8000/health` for liveness, `http://127.0.0.1:8000/ready` for local configuration readiness, and `http://127.0.0.1:8000/docs` for the interactive API documentation.

In a second terminal, start Streamlit:

```powershell
python -m streamlit run streamlit_app.py
```

The default FastAPI URL is `http://127.0.0.1:8000`. Configure another URL with the `MEMORA_API_BASE_URL` environment variable or the URL field in the Streamlit sidebar.

The Flask app remains mounted inside the unified FastAPI host; use the unified Uvicorn command for the one-URL application. For isolated legacy development, `python app.py` still starts Flask directly.

The Streamlit client is retained as an optional local Advanced UI, not as the public production interface. It calls the same `/api/advanced/...` endpoints. The public Advanced page is served from the same origin at `/level-3`.

## Docker

The single-container image runs the unified FastAPI host, which mounts Flask for legacy routes. It uses `python:3.11-slim`, installs `requirements.txt`, runs as a non-root user, exposes port 8000, uses one Uvicorn worker, and checks `/health`. Docker Compose is not required for this setup.

Build from the repository root:

```powershell
docker build -t memora-advanced-api .
```

Provide the key at runtime through an environment variable or a local environment file; neither is copied into the image. For example, with a protected local `.env` file containing `GEMINI_API_KEY`:

```powershell
docker run --rm --env-file .env -p 8000:8000 memora-advanced-api
```

The container command is equivalent to:

```text
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --workers 1
```

The Docker command also specifies `--workers 1` because the Advanced document index is held in process-local memory.

To use Streamlit with the containerized API, run Streamlit separately and set `MEMORA_API_BASE_URL` to the host address that reaches the published API port.

## Reliability and Observability

- FastAPI validates request fields with Pydantic and returns structured, user-safe HTTP errors.
- Uploads are limited to 25 MiB; blank questions, empty documents, unsupported types, and missing document indexes are rejected.
- Streamlit uses bounded health, upload, and question request timeouts and displays connection, indexing, and answer progress.
- FastAPI logs indexing start/completion, safe filename/type and page/chunk counts, retrieval/reranking counts, generation outcome, groundedness result, and failures using Python's standard logging module. It does not log document contents, questions, full prompts, or API keys.
- `/health` is a liveness check. `/ready` checks local client configuration only and does not verify external Gemini availability or make a provider call.

## Testing and Validation

Run the full tests:

```powershell
python -m pytest -q
```

The suite can also be run with the standard library test runner:

```powershell
python -m unittest discover -s tests -v
```

Additional repository checks:

```powershell
python -m compileall -q app.py fastapi_app.py api_schemas.py rag tests
node --check script.js
git diff --check
```

## Project Structure

```text
MEMORA/
|-- app.py                    # Existing Flask application
|-- fastapi_app.py            # Unified FastAPI host, mounts Flask, serves Advanced API
|-- streamlit_app.py          # Optional local Advanced Streamlit client
|-- advanced.html             # Same-origin Level 3 interface
|-- advanced.js               # Level 3 API interactions
|-- api_schemas.py            # Pydantic request models
|-- rag/
|   |-- document_processor.py # PDF/TXT/Markdown extraction
|   |-- chunker.py            # Page-aware text chunking
|   |-- embeddings.py         # Gemini embedding adapter
|   |-- vector_store.py       # FAISS index and retrieval
|   |-- query_refiner.py      # Deterministic query refinement
|   |-- reranker.py           # Local candidate reranking
|   |-- generator.py          # Grounded prompt construction
|   |-- groundedness.py       # Local evidence-overlap check
|   `-- workflow.py           # LangGraph Document Tutor workflow
|-- tests/                    # Flask/RAG/FastAPI/Streamlit tests
|-- Dockerfile                # FastAPI container
|-- .dockerignore
|-- requirements.txt
|-- index.html                # Existing Flask frontend
|-- script.js
`-- style.css
```

## Known Limitations

- FastAPI's indexed document and FAISS index are held in process-local memory. They are replaced by the next successful upload, lost on restart, and not shared across multiple worker processes. Run a single Uvicorn worker for this in-memory design.
- The local groundedness check is a lexical overlap heuristic; it can flag valid paraphrases or fail to detect a semantic contradiction. It does not make a second Gemini verification call.
- Document-question responses are delivered after generation completes. The Advanced web page and optional Streamlit UI show progress while waiting, but the current Gemini/LangGraph generation architecture does not stream answer tokens.
- Docker configuration is provided as a single-container setup. Persistent/shared indexes and multi-container orchestration are outside this milestone.
