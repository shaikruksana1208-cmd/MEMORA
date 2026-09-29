from io import BytesIO

from pypdf import PdfReader


class DocumentProcessingError(ValueError):
    """Raised when a PDF cannot be processed safely."""


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
