import os
import requests
from datetime import datetime
from typing import Optional, Dict
from urllib.parse import unquote
import logging

class DocumentRetrievalService:
    """Service for retrieving documents from URLs or other sources"""

    def __init__(self, output_dir: str = "data/raw_pdfs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    async def retrieve_document(self, url: str) -> Optional[str]:
        """
        Download PDF from URL and return local filepath.

        Args:
            url: The URL to download the PDF from

        Returns:
            Local filepath to the downloaded PDF, or None if download failed
        """
        if not url.strip():
            self.logger.warning("Empty URL provided")
            return None

        try:
            self.logger.info(f"Downloading PDF from {url}...")
            response = requests.get(url, stream=True)
            response.raise_for_status()

            # Simple filename extraction
            filename = 'document.pdf'
            if 'Content-Disposition' in response.headers:
                content_disposition = response.headers['Content-Disposition']
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"\'')

            # Generate a unique filename if needed
            base_filename = os.path.basename(filename)
            filepath = os.path.join(self.output_dir, base_filename)

            # If file exists, add a timestamp to make it unique
            if os.path.exists(filepath):
                name, ext = os.path.splitext(base_filename)
                timestamp = int(datetime.now().timestamp())
                filepath = os.path.join(self.output_dir, f"{name}_{timestamp}{ext}")

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.logger.info(f"PDF downloaded to {filepath}")
            return filepath

        except Exception as e:
            self.logger.error(f"Error downloading PDF: {e}")
            return None

    async def retrieve_documents(self, urls: Dict[str, str]) -> Dict[str, str]:
        """
        Download multiple PDFs from URLs in parallel

        Args:
            urls: Dictionary mapping document IDs to URLs

        Returns:
            Dictionary mapping document IDs to local filepaths
        """
        import asyncio

        pdf_paths = {}
        tasks = []

        for doc_id, url in urls.items():
            if url.strip():
                tasks.append(self.retrieve_document(url))

        # Execute downloads in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, (doc_id, _) in enumerate([(k, v) for k, v in urls.items() if v.strip()]):
            result = results[i]
            if isinstance(result, Exception):
                self.logger.error(f"Failed to download PDF for {doc_id}: {result}")
            elif result:
                pdf_paths[doc_id] = result

        return pdf_paths
