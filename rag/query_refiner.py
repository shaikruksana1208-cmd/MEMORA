import re
from pathlib import Path


_LEADING_FILLER = re.compile(
    r"^(?:(?:hey|hi|okay|ok|so|um|uh)[,:]?\s+)+",
    re.IGNORECASE
)
_CONVERSATIONAL_LEAD_INS = re.compile(
    r"^(?:(?:can|could|would) you\s+(?:please\s+)?"
    r"(?:explain|describe|clarify|summarize|tell me about)|"
    r"(?:please\s+)?(?:explain|describe|clarify|summarize))\s+",
    re.IGNORECASE
)
_DOCUMENT_TAIL = re.compile(
    r"\s+(?:in|from|within)\s+(?:the\s+)?(?:uploaded\s+)?document[?.!]*$",
    re.IGNORECASE
)
_VAGUE_QUERY = re.compile(
    r"^(?:it|this|that|this topic|that topic|the topic|the document|"
    r"this document|that document|what about it|what about this)[?.!]*$",
    re.IGNORECASE
)


def refine_query(question, document_filename=None):
    """Clarify common conversational phrasing without answering the question."""
    original = str(question or "").strip()
    if not original:
        return original

    refined = _LEADING_FILLER.sub("", original)
    refined = _CONVERSATIONAL_LEAD_INS.sub("", refined)
    refined = _DOCUMENT_TAIL.sub("", refined)
    refined = re.sub(r"\s+", " ", refined).strip(" \t\r\n?!.:,;")

    if not refined or _VAGUE_QUERY.fullmatch(refined):
        if document_filename:
            document_topic = Path(document_filename).stem.replace("_", " ").replace("-", " ").strip()
            if document_topic:
                return f"information about {document_topic}"
        return original

    return refined