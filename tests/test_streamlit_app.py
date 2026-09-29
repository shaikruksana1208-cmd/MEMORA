import unittest
from unittest.mock import Mock, patch

import requests

from streamlit_app import APIRequestError, ask_document, check_api_health, upload_document


class StreamlitAPIHelperTests(unittest.TestCase):
    def test_health_request_uses_configured_url(self):
        response = Mock(ok=True)
        response.json.return_value = {"status": "ok", "service": "MEMORA FastAPI"}
        with patch("streamlit_app.requests.get", return_value=response) as get:
            result = check_api_health("http://localhost:8000/")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(get.call_args.args[0], "http://localhost:8000/health")
        self.assertEqual(get.call_args.kwargs["timeout"], (2, 5))

    def test_upload_sends_multipart_file_with_timeout(self):
        response = Mock(ok=True)
        response.json.return_value = {
            "success": True,
            "filename": "notes.md",
            "pages": 1,
            "chunks": 2,
        }
        with patch("streamlit_app.requests.post", return_value=response) as post:
            result = upload_document("http://localhost:8000", "notes.md", b"# Notes")

        self.assertTrue(result["success"])
        self.assertEqual(post.call_args.args[0], "http://localhost:8000/api/index-document")
        self.assertEqual(post.call_args.kwargs["files"]["file"], ("notes.md", b"# Notes", "text/markdown"))
        self.assertEqual(post.call_args.kwargs["timeout"], (5, 120))

    def test_upload_rejects_unsupported_and_empty_files_locally(self):
        with self.assertRaisesRegex(APIRequestError, "PDF, TXT, or Markdown"):
            upload_document("http://localhost:8000", "notes.docx", b"content")
        with self.assertRaisesRegex(APIRequestError, "empty"):
            upload_document("http://localhost:8000", "notes.txt", b"")

    def test_upload_and_question_enforce_service_limits(self):
        with patch("streamlit_app.MAX_UPLOAD_BYTES", 4):
            with self.assertRaisesRegex(APIRequestError, "25 MB upload limit"):
                upload_document("http://localhost:8000", "notes.txt", b"12345")
        with patch("streamlit_app.MAX_QUESTION_LENGTH", 4):
            with self.assertRaisesRegex(APIRequestError, "2000 characters"):
                ask_document("http://localhost:8000", "12345")

    def test_question_sends_json_and_rejects_blank_input(self):
        response = Mock(ok=True)
        response.json.return_value = {"success": True, "answer": "Study answer", "sources": []}
        with patch("streamlit_app.requests.post", return_value=response) as post:
            result = ask_document("http://localhost:8000", "  Explain this.  ")

        self.assertEqual(result["answer"], "Study answer")
        self.assertEqual(post.call_args.kwargs["json"], {"question": "Explain this."})
        self.assertEqual(post.call_args.kwargs["timeout"], (5, 120))
        with self.assertRaisesRegex(APIRequestError, "Enter a question"):
            ask_document("http://localhost:8000", "   ")

    def test_api_error_and_unavailable_server_are_reported(self):
        error_response = Mock(ok=False)
        error_response.json.return_value = {"error": "No document indexed."}
        with patch("streamlit_app.requests.post", return_value=error_response):
            with self.assertRaisesRegex(APIRequestError, "No document indexed"):
                ask_document("http://localhost:8000", "Question")

        with patch("streamlit_app.requests.get", side_effect=requests.ConnectionError):
            with self.assertRaisesRegex(APIRequestError, "server is unavailable"):
                check_api_health("http://localhost:8000")


if __name__ == "__main__":
    unittest.main()