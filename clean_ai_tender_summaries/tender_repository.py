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
                'ai_doc': None,
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
