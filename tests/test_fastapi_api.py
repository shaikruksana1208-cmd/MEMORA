import unittest
import logging
from io import BytesIO
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

import fastapi_app
import app as flask_app


class FastAPIApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(fastapi_app.app)

    def test_health_endpoint_remains_available(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "status": "ok",
            "service": "MEMORA FastAPI",
        })

    def test_level_one_flask_landing_and_assets_are_mounted(self):
        landing = self.client.get("/")
        css = self.client.get("/style.css")
        javascript = self.client.get("/script.js")

        self.assertEqual(landing.status_code, 200)
        self.assertIn("Level 1", landing.text)
        self.assertIn("Level 2", landing.text)
        self.assertIn("Level 3", landing.text)
        self.assertEqual(css.status_code, 200)
        self.assertIn(".level-grid", css.text)
        self.assertEqual(javascript.status_code, 200)

    def test_level_three_page_and_script_are_served_by_fastapi(self):
        page = self.client.get("/level-3")
        script = self.client.get("/advanced.js")

        self.assertEqual(page.status_code, 200)
        self.assertIn("Advanced RAG Assistant", page.text)
        self.assertIn("/api/advanced/index-document", script.text)
        self.assertIn("/api/advanced/document-question", script.text)

    def test_fastapi_schema_namespaces_advanced_routes(self):
        paths = fastapi_app.app.openapi()["paths"]

        self.assertIn("/api/advanced/index-document", paths)
        self.assertIn("/api/advanced/document-question", paths)
        self.assertNotIn("/api/index-document", paths)
        self.assertNotIn("/api/document-question", paths)
        self.assertIn("/api/index-document", {
            rule.rule for rule in flask_app.app.url_map.iter_rules()
        })
        self.assertIn("/api/document-question", {
            rule.rule for rule in flask_app.app.url_map.iter_rules()
        })

    def test_readiness_checks_local_client_without_calling_gemini(self):
        with patch("fastapi_app.client", object()):
            response = self.client.get("/ready")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ready", "service": "MEMORA API"})

        with patch("fastapi_app.client", None):
            response = self.client.get("/ready")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["status"], "not_ready")

        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json()["status"], "ok")

    def test_document_question_rejects_missing_or_blank_question(self):
        for payload in ({}, {"question": "   "}):
            with self.subTest(payload=payload):
                response = self.client.post("/api/advanced/document-question", json=payload)
                self.assertEqual(response.status_code, 422)
                self.assertEqual(set(response.json()), {"error"})

    def test_document_question_requires_indexed_document(self):
        with patch.dict(fastapi_app.FASTAPI_DOCUMENT_INDEX, {
            "index": None,
            "metadata": [],
        }):
            response = self.client.post(
                "/api/advanced/document-question",
                json={"question": "What is normalization?"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Please index a document", response.json()["error"])

    @patch("fastapi_app.build_faiss_index")
    @patch("fastapi_app.embed_texts", return_value=[[0.1, 0.2, 0.3]])
    def test_index_document_accepts_txt(self, mock_embed, mock_build_index):
        index = object()
        metadata = [{
            "filename": "notes.txt",
            "page_number": 1,
            "chunk_text": "Normalization reduces redundancy.",
            "chunk_id": "notes.txt-p1-c1",
        }]
        mock_build_index.return_value = (index, metadata)

        with patch.dict(fastapi_app.FASTAPI_DOCUMENT_INDEX, {
            "filename": None, "pages": 0, "chunks": 0, "index": None, "metadata": []
        }):
            response = self.client.post(
                "/api/advanced/index-document",
                files={"file": ("notes.txt", b"Normalization reduces redundancy.", "text/plain")},
            )
            self.assertEqual(fastapi_app.FASTAPI_DOCUMENT_INDEX["index"], index)
            self.assertEqual(fastapi_app.FASTAPI_DOCUMENT_INDEX["page_records"], [{
                "filename": "notes.txt",
                "page_number": 1,
                "page_text": "Normalization reduces redundancy.",
            }])

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "success": True,
            "filename": "notes.txt",
            "pages": 1,
            "chunks": 1,
        })
        self.assertEqual(mock_build_index.call_args.args[0][0]["filename"], "notes.txt")
        self.assertEqual(mock_build_index.call_args.args[0][0]["page_number"], 1)
        self.assertEqual(mock_build_index.call_args.args[0][0]["text"], "Normalization reduces redundancy.")
        mock_embed.assert_called_once()

    @patch("fastapi_app.build_faiss_index")
    @patch("fastapi_app.embed_texts", return_value=[[0.1, 0.2, 0.3]])
    def test_index_document_accepts_markdown(self, mock_embed, mock_build_index):
        mock_build_index.return_value = (object(), [{"filename": "notes.md", "page_number": 1}])

        with patch.dict(fastapi_app.FASTAPI_DOCUMENT_INDEX, {
            "filename": None, "pages": 0, "chunks": 0, "index": None, "metadata": []
        }):
            response = self.client.post(
                "/api/advanced/index-document",
                files={"file": ("notes.md", b"# Notes\n\nImportant details.", "text/markdown")},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["filename"], "notes.md")
        self.assertEqual(mock_build_index.call_args.args[0][0]["page_number"], 1)
        self.assertTrue(mock_embed.called)

    def test_index_document_rejects_unsupported_extension(self):
        response = self.client.post(
            "/api/advanced/index-document",
            files={"file": ("notes.docx", b"Document", "application/octet-stream")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("Unsupported file type", response.json()["error"])

    def test_index_document_rejects_empty_document(self):
        response = self.client.post(
            "/api/advanced/index-document",
            files={"file": ("empty.txt", b"  \n\t", "text/plain")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("empty", response.json()["error"].lower())

    def test_index_document_rejects_missing_upload(self):
        response = self.client.post("/api/index-document")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Please upload", response.json()["error"])

    @patch("app.build_faiss_index", return_value=(object(), [{"filename": "level-two.txt"}]))
    @patch("app.embed_texts", return_value=[[0.1, 0.2, 0.3]])
    def test_level_two_flask_document_upload_remains_available(self, mock_embed, mock_build):
        with patch.dict(flask_app.DOCUMENT_INDEX, {
            "filename": None,
            "pages": 0,
            "chunks": 0,
            "index": None,
            "metadata": [],
        }):
            response = self.client.post(
                "/api/index-document",
                files={"file": ("level-two.txt", b"Level two document content.", "text/plain")},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["filename"], "level-two.txt")
        mock_embed.assert_called_once()
        mock_build.assert_called_once()

    def test_level_two_and_advanced_index_paths_do_not_collide(self):
        with (
            patch.dict(flask_app.DOCUMENT_INDEX, {
                "filename": None, "pages": 0, "chunks": 0, "index": None, "metadata": []
            }),
            patch.dict(fastapi_app.FASTAPI_DOCUMENT_INDEX, {
                "filename": None, "pages": 0, "chunks": 0, "page_records": [], "index": None, "metadata": []
            }),
        ):
            level_two_response = self.client.post("/api/index-document")
            advanced_response = self.client.post("/api/advanced/index-document")

        self.assertEqual(level_two_response.status_code, 400)
        self.assertEqual(advanced_response.status_code, 400)
        self.assertEqual(level_two_response.json()["error"], "Please upload a document first.")
        self.assertEqual(advanced_response.json()["error"], "Please upload a document first.")

    def test_index_document_rejects_upload_over_size_limit(self):
        with patch("fastapi_app.MAX_UPLOAD_BYTES", 8):
            response = self.client.post(
                "/api/advanced/index-document",
                files={"file": ("notes.txt", b"123456789", "text/plain")},
            )

        self.assertEqual(response.status_code, 413)
        self.assertIn("25 MB", response.json()["error"])

    @patch("fastapi_app.build_faiss_index")
    @patch("fastapi_app.embed_texts", return_value=[[0.1, 0.2, 0.3]])
    def test_indexing_logs_metadata_but_not_document_content(self, mock_embed, mock_build_index):
        mock_build_index.return_value = (object(), [{"filename": "private-notes.txt"}])
        with patch.dict(fastapi_app.FASTAPI_DOCUMENT_INDEX, {
            "filename": None, "pages": 0, "chunks": 0,
            "page_records": [], "index": None, "metadata": []
        }), self.assertLogs("fastapi_app", level=logging.INFO) as captured:
            response = self.client.post(
                "/api/advanced/index-document",
                files={"file": ("private-notes.txt", b"secret document body", "text/plain")},
            )

        logs = "\n".join(captured.output)
        self.assertEqual(response.status_code, 200)
        self.assertIn("private-notes.txt", logs)
        self.assertIn("type=txt", logs)
        self.assertIn("pages=1", logs)
        self.assertIn("chunks=1", logs)
        self.assertNotIn("secret document body", logs)

    @patch("fastapi_app.build_faiss_index")
    @patch("fastapi_app.embed_texts", return_value=[[0.1, 0.2, 0.3]])
    def test_question_uses_document_created_by_fastapi_index_endpoint(self, mock_embed, mock_build_index):
        index = object()
        metadata = [{
            "filename": "notes.txt",
            "page_number": 1,
            "chunk_text": "Normalization reduces redundancy.",
            "chunk_id": "notes.txt-p1-c1",
        }]
        mock_build_index.return_value = (index, metadata)
        workflow = Mock()
        workflow.invoke.return_value = {
            "answer": "Normalization reduces redundancy.",
            "sources": [{"filename": "notes.txt", "page": 1}],
        }

        with (
            patch.dict(fastapi_app.FASTAPI_DOCUMENT_INDEX, {
                "filename": None, "pages": 0, "chunks": 0, "index": None, "metadata": []
            }),
            patch("fastapi_app.create_document_tutor_workflow", return_value=workflow),
        ):
            index_response = self.client.post(
                "/api/advanced/index-document",
                files={"file": ("notes.txt", b"Normalization reduces redundancy.", "text/plain")},
            )
            question_response = self.client.post(
                "/api/advanced/document-question",
                json={"question": "What is normalization?"},
            )

        self.assertEqual(index_response.status_code, 200)
        self.assertEqual(question_response.status_code, 200)
        state = workflow.invoke.call_args.args[0]
        self.assertIs(state["document_index"], index)
        self.assertEqual(state["metadata"], metadata)
        self.assertEqual(question_response.json()["sources"], [{"filename": "notes.txt", "page": 1}])

    def test_document_question_invokes_workflow_and_preserves_response_shape(self):
        expected_result = {
            "answer": "Normalization reduces redundancy.",
            "sources": [{"filename": "DBMS_Unit1.pdf", "page": 2}],
        }
        workflow = Mock()
        workflow.invoke.return_value = expected_result
        indexed_document = {
            "index": object(),
            "metadata": [{"filename": "DBMS_Unit1.pdf", "page_number": 2}],
            "filename": "DBMS_Unit1.pdf",
        }

        with (
            patch.dict(fastapi_app.FASTAPI_DOCUMENT_INDEX, indexed_document),
            patch("fastapi_app.create_document_tutor_workflow", return_value=workflow),
        ):
            response = self.client.post(
                "/api/advanced/document-question",
                json={"question": "What is normalization?"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "success": True,
            "answer": expected_result["answer"],
            "sources": expected_result["sources"],
        })
        state = workflow.invoke.call_args.args[0]
        self.assertEqual(state["question"], "What is normalization?")
        for dependency in (
            "generate_ai",
            "refine_query",
            "embed_texts",
            "retrieve_top_chunks",
            "rerank_chunks",
            "build_grounded_prompt",
            "is_answer_grounded",
            "unverified_answer_message",
        ):
            self.assertTrue(callable(state[dependency]), dependency)

    def test_workflow_overload_returns_service_unavailable_error(self):
        workflow = Mock()
        workflow.invoke.side_effect = RuntimeError("503 UNAVAILABLE")
        with (
            patch.dict(fastapi_app.FASTAPI_DOCUMENT_INDEX, {
                "index": object(),
                "metadata": [{"filename": "notes.txt", "page_number": 1}],
                "filename": "notes.txt",
            }),
            patch("fastapi_app.create_document_tutor_workflow", return_value=workflow),
        ):
            response = self.client.post(
                "/api/advanced/document-question",
                json={"question": "Summarize the notes."},
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(set(response.json()), {"error"})

    def test_unexpected_workflow_error_does_not_leak_details(self):
        workflow = Mock()
        workflow.invoke.side_effect = RuntimeError("internal API key secret-value")
        with (
            patch.dict(fastapi_app.FASTAPI_DOCUMENT_INDEX, {
                "index": object(),
                "metadata": [{"filename": "notes.txt", "page_number": 1}],
                "filename": "notes.txt",
            }),
            patch("fastapi_app.create_document_tutor_workflow", return_value=workflow),
        ):
            response = self.client.post(
                "/api/advanced/document-question",
                json={"question": "Question containing private text"},
            )

        self.assertEqual(response.status_code, 500)
        self.assertNotIn("secret-value", response.text)
        self.assertNotIn("private text", response.text)

    def test_workflow_observability_logs_counts_without_sensitive_text(self):
        evidence = [{"chunk_text": "Normalization reduces redundancy."}]
        with (
            patch("fastapi_app.retrieve_top_chunks", return_value=evidence),
            patch("fastapi_app.rerank_chunks", return_value=evidence),
            patch("fastapi_app.generate_ai", return_value="Sensitive generated answer."),
            patch("fastapi_app.is_answer_grounded", return_value=True),
            self.assertLogs("fastapi_app", level=logging.INFO) as captured,
        ):
            fastapi_app._logged_retrieve_top_chunks(object(), [], [0.1], top_k=12)
            fastapi_app._logged_rerank_chunks("private query", evidence, top_k=4)
            fastapi_app._logged_generate_ai("private prompt")
            fastapi_app._logged_groundedness_check("Sensitive generated answer.", evidence)

        logs = "\n".join(captured.output)
        self.assertIn("candidate_count=1", logs)
        self.assertIn("selected_count=1", logs)
        self.assertIn("Document answer generation succeeded", logs)
        self.assertIn("grounded=True", logs)
        self.assertNotIn("private query", logs)
        self.assertNotIn("private prompt", logs)
        self.assertNotIn("Sensitive generated answer", logs)
        self.assertNotIn("Normalization reduces redundancy", logs)


if __name__ == "__main__":
    unittest.main()