import unittest
from io import BytesIO
from unittest.mock import patch

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app import app
from rag.document_processor import DocumentProcessingError, extract_document_pages


class DocumentProcessorTests(unittest.TestCase):
    def make_text_pdf(self):
        writer = PdfWriter()
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({
            NameObject("/Type"): NameObject("/Font"),
            NameObject("/Subtype"): NameObject("/Type1"),
            NameObject("/BaseFont"): NameObject("/Helvetica")
        })
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({
                NameObject("/F1"): writer._add_object(font)
            })
        })
        content = DecodedStreamObject()
        content.set_data(b"BT /F1 12 Tf 72 720 Td (PDF extraction works) Tj ET")
        page[NameObject("/Contents")] = writer._add_object(content)
        output = BytesIO()
        writer.write(output)
        return output.getvalue()

    def test_extracts_valid_pdf_with_existing_page_structure(self):
        pages = extract_document_pages(self.make_text_pdf(), "notes.pdf")
        self.assertEqual(pages, [{
            "filename": "notes.pdf",
            "page_number": 1,
            "page_text": "PDF extraction works"
        }])

    def test_extracts_valid_txt_as_single_document(self):
        pages = extract_document_pages(b"  First line\nSecond line  ", "notes.txt")
        self.assertEqual(pages, [{
            "filename": "notes.txt",
            "page_number": 1,
            "page_text": "First line\nSecond line"
        }])

    def test_extracts_valid_markdown_as_single_document(self):
        markdown = b"# Heading\n\n- First point\n- Second point"
        pages = extract_document_pages(markdown, "notes.md")
        self.assertEqual(pages, [{
            "filename": "notes.md",
            "page_number": 1,
            "page_text": "# Heading\n\n- First point\n- Second point"
        }])

    def test_rejects_empty_txt_and_markdown(self):
        for filename in ("empty.txt", "empty.md"):
            with self.subTest(filename=filename):
                with self.assertRaisesRegex(DocumentProcessingError, "file is empty"):
                    extract_document_pages(b"  \n\t", filename)

    def test_rejects_unsupported_extension(self):
        with self.assertRaisesRegex(DocumentProcessingError, "Unsupported file type"):
            extract_document_pages(b"content", "notes.docx")


class DocumentTutorValidationTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_document_requires_upload(self):
        response = self.client.post('/api/index-document', data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Please upload a document first', response.get_json()['error'])

    @patch('app.build_faiss_index', return_value=(object(), [{'chunk_text': 'Text note content.'}]))
    @patch('app.embed_texts', return_value=[[0.1, 0.2, 0.3]])
    def test_index_document_accepts_txt(self, mock_embed_texts, mock_build_index):
        with patch('app.DOCUMENT_INDEX', {
            'filename': None,
            'pages': 0,
            'chunks': 0,
            'index': None,
            'metadata': []
        }):
            response = self.client.post('/api/index-document', data={
                'file': (BytesIO(b'Text note content.'), 'notes.txt')
            }, content_type='multipart/form-data')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['filename'], 'notes.txt')
        self.assertEqual(response.get_json()['pages'], 1)
        mock_embed_texts.assert_called_once()
        mock_build_index.assert_called_once()

    def test_document_question_requires_indexed_document(self):
        response = self.client.post('/api/document-question', json={'question': 'What is normalization?'})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Please index a document before asking a question', response.get_json()['error'])

    @patch('app.generate_ai', return_value='Normalization reduces redundancy.')
    @patch('app.retrieve_top_chunks', return_value=[{
        'filename': 'DBMS_Unit1.pdf',
        'page_number': 1,
        'chunk_id': 'DBMS_Unit1.pdf-p1-c1',
        'chunk_text': 'Normalization reduces redundancy.'
    }])
    @patch('app.embed_texts', return_value=[[0.1, 0.2, 0.3]])
    def test_document_question_success_path(self, mock_embed_texts, mock_retrieve, mock_generate):
        with patch('app.DOCUMENT_INDEX', {
            'filename': 'DBMS_Unit1.pdf',
            'pages': 1,
            'chunks': 1,
            'index': object(),
            'metadata': [{'filename': 'DBMS_Unit1.pdf', 'page_number': 1, 'chunk_text': 'Normalization reduces redundancy.', 'chunk_id': 'DBMS_Unit1.pdf-p1-c1'}]
        }):
            response = self.client.post('/api/document-question', json={'question': 'What is normalization?'})
            self.assertEqual(response.status_code, 200)
            payload = response.get_json()
            self.assertTrue(payload['success'])
            self.assertIn('Normalization', payload['answer'])
            self.assertEqual(payload['sources'][0]['page'], 1)

    @patch('app.generate_ai', side_effect=Exception('503 UNAVAILABLE. This model is currently experiencing high demand.'))
    @patch('app.retrieve_top_chunks', return_value=[{
        'filename': 'DBMS_Unit1.pdf',
        'page_number': 1,
        'chunk_id': 'DBMS_Unit1.pdf-p1-c1',
        'chunk_text': 'Normalization reduces redundancy.'
    }])
    @patch('app.embed_texts', return_value=[[0.1, 0.2, 0.3]])
    def test_document_question_generation_error_path(self, mock_embed_texts, mock_retrieve, mock_generate):
        with patch('app.DOCUMENT_INDEX', {
            'filename': 'DBMS_Unit1.pdf',
            'pages': 1,
            'chunks': 1,
            'index': object(),
            'metadata': [{'filename': 'DBMS_Unit1.pdf', 'page_number': 1, 'chunk_text': 'Normalization reduces redundancy.', 'chunk_id': 'DBMS_Unit1.pdf-p1-c1'}]
        }):
            response = self.client.post('/api/document-question', json={'question': 'What is normalization?'})
            self.assertEqual(response.status_code, 503)
            self.assertIn('Gemini is busy right now', response.get_json()['error'])


if __name__ == '__main__':
    unittest.main()
