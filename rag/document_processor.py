from io import BytesIO
from pathlib import Path

from pypdf import PdfReader


class DocumentProcessingError(ValueError):
    """Raised when an uploaded document cannot be processed safely."""


def _extract_text_document(file_bytes, filename, extension):
    if not file_bytes or not file_bytes.strip():
        raise DocumentProcessingError(
            f"The uploaded {extension.upper()} file is empty."
        )

    try:
        page_text = file_bytes.decode("utf-8-sig").strip()
    except UnicodeDecodeError as exc:
        raise DocumentProcessingError(
            f"The {extension.upper()} file must use UTF-8 text encoding."
        ) from exc

    if not page_text:
        raise DocumentProcessingError(
            f"The uploaded {extension.upper()} file is empty."
        )

    return [{
        "filename": filename,
        "page_number": 1,
        "page_text": page_text
    }]


def extract_pdf_pages(file_bytes, filename):
    if not file_bytes:
        raise DocumentProcessingError("The uploaded PDF is empty.")

    try:
        reader = PdfReader(BytesIO(file_bytes))
    except Exception as exc:  # pragma: no cover - defensive path
        raise DocumentProcessingError(
            "The PDF could not be opened. Please upload a valid PDF."
        ) from exc

    pages = []

    if len(reader.pages) == 0:
        raise DocumentProcessingError(
            "The document does not contain extractable text."
        )

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            page_text = page.extract_text() or ""
        except Exception:
            page_text = ""

        clean_text = "\n".join(
            line.strip() for line in page_text.splitlines() if line.strip()
        ).strip()

        pages.append({
            "filename": filename,
            "page_number": page_number,
            "page_text": clean_text
        })

    if not any(page["page_text"] for page in pages):
        raise DocumentProcessingError(
            "The document does not contain extractable text."
        )

    return pages


def extract_document_pages(file_bytes, filename):
    extension = Path(filename).suffix.lower()

    if extension == ".pdf":
        return extract_pdf_pages(file_bytes, filename)
    if extension == ".txt":
        return _extract_text_document(file_bytes, filename, "txt")
    if extension == ".md":
        return _extract_text_document(file_bytes, filename, "md")

    raise DocumentProcessingError(
        "Unsupported file type. Please upload a PDF, TXT, or Markdown file."
    )
