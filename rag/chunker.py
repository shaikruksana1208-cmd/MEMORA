import re


def chunk_pages(pages, chunk_size=500, overlap=80):
    chunks = []

    for page in pages:
        page_text = (page.get("page_text") or "").strip()

        if not page_text:
            continue

        start = 0
        chunk_index = 1

        while start < len(page_text):
            end = min(start + chunk_size, len(page_text))
            chunk_text = page_text[start:end].strip()

            if not chunk_text:
                break

            chunks.append({
                "filename": page["filename"],
                "page_number": page["page_number"],
                "chunk_id": f"{page['filename']}-p{page['page_number']}-c{chunk_index}",
                "text": chunk_text
            })

            if end >= len(page_text):
                break

            start = max(start + chunk_size - overlap, end - overlap)
            chunk_index += 1

    if not chunks:
        return []

    return chunks
