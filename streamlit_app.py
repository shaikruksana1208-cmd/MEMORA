import hashlib
import os
from pathlib import Path

import requests


DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = (5, 120)
HEALTH_TIMEOUT = (2, 5)
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_QUESTION_LENGTH = 2000
SUPPORTED_EXTENSIONS = {"pdf", "txt", "md"}
UNVERIFIED_API_ERROR = "The FastAPI server returned an unreadable response."


class APIRequestError(RuntimeError):
    """Raised when a FastAPI request fails or returns an invalid response."""


def _base_url(base_url):
    return (base_url or DEFAULT_API_BASE_URL).strip().rstrip("/")


def _read_json_response(response):
    try:
        payload = response.json()
    except ValueError as error:
        raise APIRequestError(UNVERIFIED_API_ERROR) from error

    if not isinstance(payload, dict):
        raise APIRequestError(UNVERIFIED_API_ERROR)

    if not response.ok:
        raise APIRequestError(str(payload.get("error") or "FastAPI request failed."))

    return payload


def check_api_health(base_url, timeout=HEALTH_TIMEOUT):
    try:
        response = requests.get(
            f"{_base_url(base_url)}/health",
            timeout=timeout,
        )
        payload = _read_json_response(response)
    except requests.RequestException as error:
        raise APIRequestError("FastAPI server is unavailable. Check the server URL and try again.") from error

    if payload.get("status") != "ok":
        raise APIRequestError("FastAPI health check did not return an OK status.")
    return payload


def upload_document(base_url, filename, file_bytes, timeout=REQUEST_TIMEOUT):
    extension = Path(filename or "").suffix.lower().lstrip(".")
    if extension not in SUPPORTED_EXTENSIONS:
        raise APIRequestError("Please choose a PDF, TXT, or Markdown file.")
    if not file_bytes:
        raise APIRequestError("The selected document is empty.")
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise APIRequestError("The selected document exceeds the 25 MB upload limit.")

    mime_type = {
        "pdf": "application/pdf",
        "txt": "text/plain",
        "md": "text/markdown",
    }[extension]

    try:
        response = requests.post(
            f"{_base_url(base_url)}/api/advanced/index-document",
            files={"file": (filename, file_bytes, mime_type)},
            timeout=timeout,
        )
        return _read_json_response(response)
    except requests.RequestException as error:
        raise APIRequestError("FastAPI server is unavailable or the upload timed out.") from error


def ask_document(base_url, question, timeout=REQUEST_TIMEOUT):
    question = (question or "").strip()
    if not question:
        raise APIRequestError("Enter a question before asking MEMORA.")
    if len(question) > MAX_QUESTION_LENGTH:
        raise APIRequestError("Keep your question to 2000 characters or fewer.")

    try:
        response = requests.post(
            f"{_base_url(base_url)}/api/advanced/document-question",
            json={"question": question},
            timeout=timeout,
        )
        return _read_json_response(response)
    except requests.RequestException as error:
        raise APIRequestError("FastAPI server is unavailable or the request timed out.") from error


def run_app():
    import streamlit as st

    st.set_page_config(
        page_title="MEMORA Document Tutor",
        page_icon="📚",
        layout="centered",
    )
    st.markdown(
        """
        <style>
        .stApp { background: linear-gradient(145deg, #f5f8f5 0%, #edf3f2 55%, #f9f5eb 100%); }
        .block-container { max-width: 900px; padding-top: 2.2rem; }
        h1, h2, h3 { color: #173b35; }
        .memora-kicker { color: #26705d; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
        [data-testid="stMetric"] { background: rgba(255,255,255,.74); border-left: 4px solid #df9d4a; padding: .8rem 1rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="memora-kicker">MEMORA · Advanced</div>', unsafe_allow_html=True)
    st.title("Document Tutor")
    st.write("Study directly from your notes with answers grounded in the passages you upload.")

    configured_url = os.getenv("MEMORA_API_BASE_URL", DEFAULT_API_BASE_URL)
    with st.sidebar:
        st.header("Connection")
        api_base_url = st.text_input("FastAPI base URL", value=configured_url).strip()
        if st.button("Check connection", use_container_width=True):
            with st.spinner("Checking FastAPI…"):
                try:
                    health = check_api_health(api_base_url)
                    st.session_state["api_health"] = (True, health.get("service", "FastAPI"))
                except APIRequestError as error:
                    st.session_state["api_health"] = (False, str(error))
                st.session_state["api_health_url"] = api_base_url

        health_state = st.session_state.get("api_health")
        if (
            health_state is None
            or st.session_state.get("api_health_url") != api_base_url
        ):
            try:
                health = check_api_health(api_base_url)
                health_state = (True, health.get("service", "FastAPI"))
            except APIRequestError as error:
                health_state = (False, str(error))
            st.session_state["api_health"] = health_state
            st.session_state["api_health_url"] = api_base_url

        if health_state[0]:
            st.success(f"Connected · {health_state[1]}")
        else:
            st.error(health_state[1])

    st.divider()
    st.subheader("1. Add your study material")
    uploaded_file = st.file_uploader(
        "Choose a document",
        type=sorted(SUPPORTED_EXTENSIONS),
        max_upload_size=25,
        help="PDF, TXT, and Markdown files are supported.",
    )

    indexed_filename = st.session_state.get("indexed_filename")
    indexed_signature = st.session_state.get("indexed_file_signature")
    selected_signature = None
    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        selected_signature = (
            uploaded_file.name,
            hashlib.sha256(file_bytes).hexdigest(),
        )
        st.caption(f"Selected: {uploaded_file.name}")
        if st.button("Index document", type="primary", use_container_width=True):
            try:
                with st.spinner("Reading and indexing your document…"):
                    result = upload_document(api_base_url, uploaded_file.name, file_bytes)
                indexed_filename = result.get("filename", uploaded_file.name)
                st.session_state["indexed_filename"] = indexed_filename
                st.session_state["indexed_file_signature"] = selected_signature
                st.session_state.pop("last_answer", None)
                st.success(
                    f"{indexed_filename} indexed · {result.get('pages', 0)} pages · "
                    f"{result.get('chunks', 0)} chunks"
                )
            except APIRequestError as error:
                st.error(str(error))

    if indexed_filename:
        st.success(f"Ready to study: {indexed_filename}")

    st.divider()
    st.subheader("2. Ask a question")
    question = st.text_area(
        "What would you like to understand?",
        placeholder="For example: How does normalization reduce redundancy?",
        height=100,
    )
    document_ready = bool(indexed_filename and selected_signature == indexed_signature)
    if st.button("Ask MEMORA", use_container_width=True, disabled=not document_ready):
        if not question.strip():
            st.warning("Enter a question before asking MEMORA.")
        else:
            try:
                with st.spinner("Searching your document and preparing an answer…"):
                    result = ask_document(api_base_url, question)
                st.session_state["last_answer"] = result
            except APIRequestError as error:
                st.error(str(error))
    if indexed_filename and not document_ready:
        st.caption("Index the currently selected document before asking a question.")

    answer_result = st.session_state.get("last_answer")
    if answer_result:
        st.divider()
        st.subheader("MEMORA's answer")
        st.markdown(answer_result.get("answer", "No answer was returned."))
        sources = answer_result.get("sources") or []
        if sources:
            with st.expander("Sources", expanded=True):
                for source in sources:
                    source_filename = source.get("filename", "Document")
                    source_page = source.get("page")
                    page_label = f" · page {source_page}" if source_page is not None else ""
                    st.markdown(f"- **{source_filename}**{page_label}")


if __name__ == "__main__":
    run_app()