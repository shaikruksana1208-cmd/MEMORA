from fastapi import FastAPI, File, UploadFile
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.requests import Request
from starlette.responses import JSONResponse
from werkzeug.utils import secure_filename

from api_schemas import DocumentQuestionRequest
from app import (
    DOCUMENT_INDEX,
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


@app.exception_handler(RequestValidationError)
async def request_validation_error_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "Please enter a valid document question."},
    )


@app.post("/api/index-document")
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

    try:
        file_bytes = file.file.read()
        pages = extract_document_pages(file_bytes, filename)
        chunks = chunk_pages(pages, chunk_size=500, overlap=80)
        if not chunks:
            return JSONResponse(
                status_code=400,
                content={"error": "The document does not contain extractable text."},
            )

        embeddings = embed_texts([chunk["text"] for chunk in chunks], client=client)
        if not embeddings:
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

        return {
            "success": True,
            "filename": filename,
            "pages": len(pages),
            "chunks": len(chunks),
        }

    except DocumentProcessingError as error:
        return JSONResponse(status_code=400, content={"error": str(error)})

    except EmbeddingError as error:
        return JSONResponse(status_code=500, content={"error": str(error)})

    except VectorStoreError as error:
        return JSONResponse(status_code=500, content={"error": str(error)})

    except Exception:
        return JSONResponse(
            status_code=500,
            content={"error": "We couldn't index this document right now. Please try again later."},
        )


@app.post("/api/document-question")
def document_question(data: DocumentQuestionRequest):
    if not FASTAPI_DOCUMENT_INDEX["index"] or not FASTAPI_DOCUMENT_INDEX["metadata"]:
        return JSONResponse(
            status_code=400,
            content={"error": "Please index a document before asking a question."},
        )

    try:
        workflow = create_document_tutor_workflow()
        result = workflow.invoke({
            "question": data.question,
            "document_index": FASTAPI_DOCUMENT_INDEX["index"],
            "metadata": FASTAPI_DOCUMENT_INDEX["metadata"],
            "filename": FASTAPI_DOCUMENT_INDEX["filename"],
            "client": client,
            "generate_ai": generate_ai,
            "refine_query": refine_query,
            "embed_texts": embed_texts,
            "retrieve_top_chunks": retrieve_top_chunks,
            "rerank_chunks": rerank_chunks,
            "build_grounded_prompt": build_grounded_prompt,
            "is_answer_grounded": is_answer_grounded,
            "unverified_answer_message": unverified_answer_message,
        })

        return {
            "success": True,
            "answer": result.get(
                "answer",
                "I could not generate an answer from the uploaded document.",
            ),
            "sources": result.get("sources", []),
        }

    except EmbeddingError as error:
        return JSONResponse(status_code=500, content={"error": str(error)})

    except VectorStoreError as error:
        return JSONResponse(status_code=500, content={"error": str(error)})

    except Exception as error:
        error_text = str(error)
        if (
            "503" in error_text
            or "busy" in error_text.lower()
            or "unavailable" in error_text.lower()
        ):
            return JSONResponse(
                status_code=503,
                content={"error": "Gemini is busy right now. Please try again later."},
            )

        return JSONResponse(
            status_code=500,
            content={"error": "We couldn't generate an answer right now. Please try again later."},
        )