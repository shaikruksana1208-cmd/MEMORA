import os

from google import genai


class EmbeddingError(RuntimeError):
    """Raised when an embedding request fails."""


def _extract_embedding_values(response):
    if getattr(response, "embeddings", None):
        first_embedding = response.embeddings[0]

        if hasattr(first_embedding, "values"):
            return list(first_embedding.values)

        if hasattr(first_embedding, "embedding"):
            return list(first_embedding.embedding)

        if isinstance(first_embedding, dict):
            if "values" in first_embedding:
                return list(first_embedding["values"])
            if "embedding" in first_embedding:
                return list(first_embedding["embedding"])

    raise EmbeddingError("The embedding response was invalid.")


def embed_texts(texts, client=None):
    if not texts:
        return []

    if client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise EmbeddingError(
                "MEMORA AI is unavailable because GEMINI_API_KEY is not configured."
            )
        client = genai.Client(api_key=api_key)

    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=texts
        )
        embeddings = []

        for item in getattr(response, "embeddings", []):
            if hasattr(item, "values"):
                embeddings.append(list(item.values))
            elif hasattr(item, "embedding"):
                embeddings.append(list(item.embedding))
            elif isinstance(item, dict) and "values" in item:
                embeddings.append(list(item["values"]))
            elif isinstance(item, dict) and "embedding" in item:
                embeddings.append(list(item["embedding"]))

        if len(embeddings) != len(texts):
            raise EmbeddingError("The embedding response did not match the input text count.")

        return embeddings

    except Exception as exc:
        error_text = str(exc)

        if "429" in error_text or "RESOURCE_EXHAUSTED" in error_text:
            raise EmbeddingError("MEMORA AI limit has been reached. Please try again later.") from exc

        if "API key" in error_text.lower() or "unauthorized" in error_text.lower():
            raise EmbeddingError("MEMORA AI is unavailable because the API key is invalid or missing.") from exc

        raise EmbeddingError("We could not create the document embeddings right now.") from exc
