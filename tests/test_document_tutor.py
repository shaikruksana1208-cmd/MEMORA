import unittest
from unittest.mock import patch

from app import app


class DocumentTutorValidationTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_index_document_requires_pdf_upload(self):
        response = self.client.post('/api/index-document', data={})
        self.assertEqual(response.status_code, 400)
        self.assertIn('Please upload a PDF first', response.get_json()['error'])

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
