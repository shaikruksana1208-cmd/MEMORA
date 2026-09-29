import numpy as np
import faiss


class VectorStoreError(RuntimeError):
    """Raised when the FAISS index cannot be created or queried."""


def build_faiss_index(chunks, embeddings):
    if not chunks or not embeddings:
        raise VectorStoreError("No document embeddings were generated.")

    vector_matrix = np.asarray(embeddings, dtype="float32")

    if vector_matrix.ndim == 1:
        vector_matrix = vector_matrix.reshape(1, -1)

    try:
        index = faiss.IndexFlatL2(vector_matrix.shape[1])
        index.add(vector_matrix)
    except Exception as exc:
        raise VectorStoreError("We could not build the document index.") from exc

    metadata = [
        {
            "filename": chunk["filename"],
            "page_number": chunk["page_number"],
            "chunk_text": chunk["text"],
            "chunk_id": chunk["chunk_id"]
        }
        for chunk in chunks
    ]

    return index, metadata


def retrieve_top_chunks(index, metadata, query_embedding, top_k=4):
    if index is None or not metadata:
        raise VectorStoreError("Please index a document before asking a question.")

    if query_embedding is None:
        raise VectorStoreError("The question embedding could not be created.")

    try:
        vector = np.asarray([query_embedding], dtype="float32")
        distances, neighbor_ids = index.search(vector, min(top_k, len(metadata)))
    except Exception as exc:
        raise VectorStoreError("The document search failed. Please try again later.") from exc

    results = []

    for neighbor_id in neighbor_ids[0]:
        if int(neighbor_id) < 0 or int(neighbor_id) >= len(metadata):
            continue
        results.append(metadata[int(neighbor_id)])

    return results
