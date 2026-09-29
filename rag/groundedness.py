import re


_TOKEN_PATTERN = re.compile(r"[a-z0-9]+", re.IGNORECASE)
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_MARKUP_PREFIX = re.compile(r"^\s*(?:#{1,6}\s+|[-*+]\s+|\d+[.)]\s+)")
_STOPWORDS = {
    "a", "about", "above", "after", "again", "all", "also", "an", "and",
    "any", "are", "as", "at", "be", "because", "been", "before", "being",
    "between", "both", "but", "by", "can", "could", "did", "do", "does",
    "during", "each", "for", "from", "had", "has", "have", "he", "her",
    "here", "him", "his", "how", "i", "if", "in", "into", "is", "it",
    "its", "may", "might", "more", "most", "not", "of", "on", "or", "our",
    "out", "over", "she", "should", "some", "such", "than", "that", "the",
    "their", "them", "then", "there", "these", "they", "this", "those",
    "through", "to", "under", "up", "was", "we", "were", "what", "when",
    "where", "which", "while", "who", "will", "with", "would", "you", "your"
}
_UNSUPPORTED_ANSWER = (
    "I couldn't verify this answer from the retrieved passages. "
    "Please try asking about information stated in the uploaded document."
)


def _content_tokens(text):
    return {
        token.casefold()
        for token in _TOKEN_PATTERN.findall(text or "")
        if token.casefold() not in _STOPWORDS
    }


def is_answer_grounded(answer, evidence_chunks, minimum_coverage=0.5):
    """Check that each substantive answer sentence overlaps retrieved evidence."""
    if not isinstance(answer, str) or not answer.strip() or not evidence_chunks:
        return False

    evidence_text = " ".join(
        chunk.get("chunk_text", "")
        for chunk in evidence_chunks
        if isinstance(chunk, dict)
    )
    evidence_tokens = _content_tokens(evidence_text)
    if not evidence_tokens:
        return False

    substantive_sentences = []
    for line in answer.splitlines():
        cleaned_line = _MARKUP_PREFIX.sub("", line)
        substantive_sentences.extend(_SENTENCE_SPLIT.split(cleaned_line))

    checked_sentence_count = 0
    for sentence in substantive_sentences:
        sentence_tokens = _content_tokens(sentence)
        if len(sentence_tokens) < 3:
            continue

        checked_sentence_count += 1
        coverage = len(sentence_tokens.intersection(evidence_tokens)) / len(sentence_tokens)
        if coverage < minimum_coverage:
            return False

    return checked_sentence_count > 0


def unverified_answer_message():
    return _UNSUPPORTED_ANSWER