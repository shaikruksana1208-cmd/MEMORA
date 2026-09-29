import re


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "in", "is", "it", "of", "on", "or", "the", "to", "was", "were",
    "what", "when", "where", "which", "who", "why", "with"
}


def _query_tokens(query):
    return {
        token.casefold()
        for token in _TOKEN_PATTERN.findall(query or "")
        if token.casefold() not in _STOPWORDS
    }


def rerank_chunks(query, candidates, top_k=4):
    """Rerank FAISS candidates using rank retention and query-term coverage."""
    if not candidates or top_k <= 0:
        return []

    query_terms = _query_tokens(query)
    candidate_count = len(candidates)
    denominator = max(candidate_count - 1, 1)
    scored_candidates = []

    for faiss_rank, candidate in enumerate(candidates):
        normalized_rank_score = 1.0 - (faiss_rank / denominator)
        chunk_terms = _query_tokens(candidate.get("chunk_text", ""))
        lexical_coverage = (
            len(query_terms.intersection(chunk_terms)) / len(query_terms)
            if query_terms else 0.0
        )
        score = 0.7 * normalized_rank_score + 0.3 * lexical_coverage
        scored_candidates.append((score, candidate))

    scored_candidates.sort(key=lambda item: item[0], reverse=True)
    return [candidate for _, candidate in scored_candidates[:top_k]]