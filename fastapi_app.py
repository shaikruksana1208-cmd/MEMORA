import logging
from a2wsgi import WSGIMiddleware
from fastapi import FastAPI, File, UploadFile
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse
from werkzeug.utils import secure_filename

from api_schemas import DocumentQuestionRequest
from app import (
    app as flask_app,
    build_grounded_prompt,
    client,
    embed_texts,
    generate_ai,
    is_answer_grounded,
    refine_query,
    rerank_chunks,
    retrieve_top_chunks,
    unverified_answer_message,
)
from rag.embeddings import EmbeddingError
from rag.chunker import chunk_pages
from rag.document_processor import DocumentProcessingError, extract_document_pages
from rag.vector_store import VectorStoreError, build_faiss_index
from rag.workflow import create_document_tutor_workflow


app = FastAPI(
    title="MEMORA API",
    description="AI-powered personalized learning and document tutoring API",
    version="1.0.0",
)

logger = logging.getLogger(__name__)
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

FASTAPI_DOCUMENT_INDEX = {
    "filename": None,
    "pages": 0,
    "page_records": [],
    "chunks": 0,
    "index": None,
    "metadata": [],
}


class HealthResponse(BaseModel):
    status: str
    service: str


@app.get("/health", response_model=HealthResponse)
def health_check():
    return {
        "status": "ok",
        "service": "MEMORA FastAPI",
    }


@app.get("/ready")
def readiness_check():
    if client is None:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "service": "MEMORA API"},
        )
    return {"status": "ready", "service": "MEMORA API"}


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    logger.warning(
        "Request validation failed (path=%s, error_count=%d)",
        request.url.path,
        len(exc.errors()),
    )
    return JSONResponse(
        status_code=422,
        content={"error": "Please enter a valid document question."},
    )


@app.post("/api/advanced/index-document")
def index_document(file: UploadFile | None = File(default=None)):
    if file is None:
        return JSONResponse(
            status_code=400,
            content={"error": "Please upload a document first."},
        )

    filename = secure_filename(file.filename or "")
    if not filename:
        return JSONResponse(
            status_code=400,
            content={"error": "Please upload a document with a valid filename."},
        )

    if not filename.lower().endswith((".pdf", ".txt", ".md")):
        return JSONResponse(
            status_code=400,
            content={"error": "Unsupported file type. Please upload a PDF, TXT, or Markdown file."},
        )

    document_type = filename.rsplit(".", 1)[-1].lower()
    logger.info("Document indexing started (filename=%s, type=%s)", filename, document_type)

    try:
        file_bytes = file.file.read(MAX_UPLOAD_BYTES + 1)
        if len(file_bytes) > MAX_UPLOAD_BYTES:
            logger.warning(
                "Document indexing rejected (type=%s, reason=upload_too_large)",
                document_type,
            )
            return JSONResponse(
                status_code=413,
                content={"error": "The uploaded document exceeds the 25 MB limit."},
            )

        pages = extract_document_pages(file_bytes, filename)
        chunks = chunk_pages(pages, chunk_size=500, overlap=80)
        if not chunks:
            logger.warning(
                "Document processing produced no chunks (filename=%s, type=%s)",
                filename,
                document_type,
            )
            return JSONResponse(
                status_code=400,
                content={"error": "The document does not contain extractable text."},
            )

        embeddings = embed_texts([chunk["text"] for chunk in chunks], client=client)
        if not embeddings:
            logger.error("Document embedding returned no vectors (type=%s)", document_type)
            return JSONResponse(
                status_code=500,
                content={"error": "We could not create embeddings for this document."},
            )

        faiss_index, metadata = build_faiss_index(chunks, embeddings)
        FASTAPI_DOCUMENT_INDEX.update({
            "filename": filename,
            "pages": len(pages),
            "page_records": pages,
            "chunks": len(chunks),
            "index": faiss_index,
            "metadata": metadata,
        })

        logger.info(
            "Document indexing completed (filename=%s, type=%s, pages=%d, chunks=%d)",
            filename,
            document_type,
            len(pages),
            len(chunks),
        )

        return {
            "success": True,
            "filename": filename,
            "pages": len(pages),
            "chunks": len(chunks),
        }

    except DocumentProcessingError as error:
        logger.warning(
            "Document processing rejected (filename=%s, type=%s, error_type=%s)",
            filename,
            document_type,
            type(error).__name__,
        )
        return JSONResponse(status_code=400, content={"error": str(error)})

    except EmbeddingError as error:
        logger.error("Document embedding failed (type=%s)", document_type)
        return JSONResponse(status_code=500, content={"error": str(error)})

    except VectorStoreError as error:
        logger.error("Document vector index creation failed (type=%s)", document_type)
        return JSONResponse(status_code=500, content={"error": str(error)})

    except Exception as error:
        logger.error("Document indexing failed (error_type=%s)", type(error).__name__)
        return JSONResponse(
            status_code=500,
            content={"error": "We couldn't index this document right now. Please try again later."},
        )


@app.post("/api/advanced/document-question")
def document_question(data: DocumentQuestionRequest):
    if not FASTAPI_DOCUMENT_INDEX["index"] or not FASTAPI_DOCUMENT_INDEX["metadata"]:
        logger.warning("Document question rejected (reason=document_not_indexed)")
        return JSONResponse(
            status_code=400,
            content={"error": "Please index a document before asking a question."},
        )

    try:
        logger.info(
            "Document question received (document_type=%s)",
            (FASTAPI_DOCUMENT_INDEX["filename"] or "").rsplit(".", 1)[-1].lower(),
        )
        workflow = create_document_tutor_workflow()
        result = workflow.invoke({
            "question": data.question,
            "document_index": FASTAPI_DOCUMENT_INDEX["index"],
            "metadata": FASTAPI_DOCUMENT_INDEX["metadata"],
            "filename": FASTAPI_DOCUMENT_INDEX["filename"],
            "client": client,
            "generate_ai": _logged_generate_ai,
            "refine_query": refine_query,
            "embed_texts": embed_texts,
            "retrieve_top_chunks": _logged_retrieve_top_chunks,
            "rerank_chunks": _logged_rerank_chunks,
            "build_grounded_prompt": build_grounded_prompt,
            "is_answer_grounded": _logged_groundedness_check,
            "unverified_answer_message": unverified_answer_message,
        })

        sources = result.get("sources", []) or []
        answer = result.get(
            "answer",
            "I could not generate an answer from the uploaded document.",
        )
        logger.info("Document question completed (source_count=%d)", len(sources))
        return {
            "success": True,
            "answer": answer,
            "sources": sources,
        }

    except EmbeddingError as error:
        logger.error("Document question embedding failed (error_type=%s)", type(error).__name__)
        return JSONResponse(status_code=500, content={"error": str(error)})

    except VectorStoreError as error:
        logger.error("Document retrieval failed (error_type=%s)", type(error).__name__)
        return JSONResponse(status_code=500, content={"error": str(error)})

    except Exception as error:
        error_text = str(error)
        if (
            "503" in error_text
            or "busy" in error_text.lower()
            or "unavailable" in error_text.lower()
        ):
            logger.warning("Document question service unavailable (error_type=%s)", type(error).__name__)
            return JSONResponse(
                status_code=503,
                content={"error": "Gemini is busy right now. Please try again later."},
            )

        logger.error("Document question failed (error_type=%s)", type(error).__name__)
        return JSONResponse(
            status_code=500,
            content={"error": "We couldn't generate an answer right now. Please try again later."},
        )


def _logged_retrieve_top_chunks(index, metadata, query_embedding, top_k=4):
    try:
        candidates = retrieve_top_chunks(index, metadata, query_embedding, top_k=top_k)
    except Exception as error:
        logger.error("Document retrieval failed (error_type=%s)", type(error).__name__)
        raise
    logger.info("Document retrieval completed (candidate_count=%d)", len(candidates))
    return candidates


def _logged_rerank_chunks(query, candidates, top_k=4):
    try:
        ranked = rerank_chunks(query, candidates, top_k=top_k)
    except Exception as error:
        logger.warning("Document reranking failed; workflow fallback will be used (error_type=%s)", type(error).__name__)
        raise
    logger.info("Document reranking completed (candidate_count=%d, selected_count=%d)", len(candidates), len(ranked))
    return ranked


def _logged_generate_ai(prompt):
    try:
        answer = generate_ai(prompt)
        logger.info("Document answer generation succeeded")
        return answer
    except Exception as error:
        logger.error("Document answer generation failed (error_type=%s)", type(error).__name__)
        raise


def _logged_groundedness_check(answer, evidence_chunks):
    try:
        grounded = is_answer_grounded(answer, evidence_chunks)
    except Exception as error:
        logger.error("Document groundedness check failed (error_type=%s)", type(error).__name__)
        raise
    logger.info(
        "Document groundedness check completed (grounded=%s, evidence_chunk_count=%d)",
        grounded,
        len(evidence_chunks),
    )
    return grounded


@app.get("/level-3", include_in_schema=False)
def advanced_page():
    return FileResponse("advanced.html")


@app.get("/advanced.js", include_in_schema=False)
def advanced_javascript():
    return FileResponse("advanced.js", media_type="application/javascript")


# Keep this fallback last so FastAPI endpoints above take precedence while
# all existing Flask routes and static files remain available at their paths.
app.mount("/", WSGIMiddleware(flask_app), name="flask-legacy")