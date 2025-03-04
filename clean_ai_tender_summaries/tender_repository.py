from typing import Dict, List, Optional, Any
from datetime import datetime

class TenderRepository:
    """
    Data access layer for tender-related operations.
    This is a mock implementation since we don't have a real database yet.
    """

    def __init__(self):
        # Mock database tables
        self._tenders = {}
        self._client_tenders = {}
        self._initialize_test_data()

    def _initialize_test_data(self):
        """Initialize test data with pre-populated markdown paths"""
        test_tender_id = "10/2024/CONM-CEE"
        test_client_id = "client123"

        # Set up test tender with pre-populated markdown paths
        self._tenders[test_tender_id] = {
            'id': test_tender_id,
            'document_urls': {
                'doc1': "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?DocumentIdParam=cGvQdaF/qmEnKvN211kkZep9eLYPa5sPlu0VFp1fA/h5Fg1pTaKl4FN73msJksylIVq1IvdI5PofzpP36PwDr6Jmx2BDu2S/t4P9dvlPFULfdyQgZAdTm3EfcUAC7CJ6&cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D",
                'doc2': "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?DocumentIdParam=z/ghU5864J3UKnVAwwWNrCp9Nvi9o32DrO2HfqSQ/7y0QPTDGl%2BTgSxAzGaBF9hR0w94oIWtN2EkYA0Og4DmgZLmV7aY3ZdlQ8%2BxtPvjDpeB0nvVKRzfe4rpHcnlPhSZ&cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D",
            },
            'markdown_paths': {
                'doc1': "data/markdown/DOC_CN2024-001193585_1741072724.md",
                'doc2': "data/markdown/DOC20241111091415Pliego_de_prescripciones_tecnicas_1741072725.md",
                'doc3': "data/markdown/DOC20241111092201Pliego_de_clausulas_administrativas.md",
                'doc4': "data/markdown/DOC20241111094338ANEXO_I.md",
                'doc5': "data/markdown/DOC20241111094425ANEXO_II.md"
            },
            'ai_summary': None,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

    def get_tender_by_id(self, tender_id: str) -> Dict[str, Any]:
        """Retrieve a tender by its ID"""
        # In a real implementation, this would query the database
        if tender_id not in self._tenders:
            # For testing, create a mock tender if it doesn't exist
            self._tenders[tender_id] = {
                'id': tender_id,
                'document_urls': [],
                'markdown_paths': {},
                'ai_summary': None,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        return self._tenders[tender_id]

    def get_client_tender(self, tender_id: str, client_id: str) -> Dict[str, Any]:
        """Retrieve a client-specific tender"""
        key = f"{client_id}:{tender_id}"
        if key not in self._client_tenders:
            # For testing, create a mock client_tender if it doesn't exist
            self._client_tenders[key] = {
                'tender_id': tender_id,
                'client_id': client_id,
                'ai_doc_path': None,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
        return self._client_tenders[key]

    def update_markdown_paths(self, tender_id: str, new_md_paths: Dict[str, str]) -> Dict[str, Any]:
        """Update the markdown paths for a tender"""
        if tender_id not in self._tenders:
            raise ValueError(f"Tender with ID {tender_id} not found")

        tender = self._tenders[tender_id]
        # Merge new paths with existing ones
        tender['markdown_paths'].update(new_md_paths)
        tender['updated_at'] = datetime.now()
        return tender

    def update_ai_summary(self, tender_id: str, ai_summary: str) -> Dict[str, Any]:
        """Update the AI summary for a tender"""
        if tender_id not in self._tenders:
            raise ValueError(f"Tender with ID {tender_id} not found")

        tender = self._tenders[tender_id]
        tender['ai_summary'] = ai_summary
        tender['updated_at'] = datetime.now()
        return tender

    def update_ai_doc(self, tender_id: str, client_id: str, ai_doc_path: str) -> Dict[str, Any]:
        """Update the client-specific AI document path for a tender"""
        key = f"{client_id}:{tender_id}"
        if key not in self._client_tenders:
            raise ValueError(f"Client tender with ID {key} not found")

        client_tender = self._client_tenders[key]
        client_tender['ai_doc_path'] = ai_doc_path  # Store path instead of content
        client_tender['updated_at'] = datetime.now()
        return client_tender
