import os
import time
import requests
import logging
from typing import Optional, Dict

class DocumentConversionService:
    """Service for converting PDFs to markdown using Marker API"""

    def __init__(self, api_key: str, output_dir: str = "data/markdown"):
        self.api_key = api_key
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.logger = logging.getLogger(__name__)

        # API endpoints
        self.submit_url = "https://www.datalab.to/api/v1/marker"

    async def convert_to_markdown(self, pdf_path: str) -> Optional[str]:
        """
        Convert PDF to markdown using the Marker API

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Path to the output markdown file if successful, None otherwise
        """
        if not os.path.exists(pdf_path):
            self.logger.error(f"Error: File not found - {pdf_path}")
            return None

        # Check if markdown file already exists
        output_filename = os.path.basename(pdf_path).replace('.pdf', '.md')
        output_path = os.path.join(self.output_dir, output_filename)

        if os.path.exists(output_path):
            self.logger.info(f"Markdown file already exists: {output_path}")
            return output_path

        try:
            # Prepare the file for upload
            with open(pdf_path, 'rb') as f:
                files = {'file': (os.path.basename(pdf_path), f, 'application/pdf')}

                # Set up the request
                headers = {
                    'accept': 'application/json',
                    'X-API-Key': self.api_key
                }

                data = {
                    'output_format': 'markdown',
                    'disable_image_extraction': 'true',
                    'paginate': 'false',
                    'skip_cache': 'false'
                }

                # Submit the PDF for processing
                self.logger.info(f"Submitting {pdf_path} to Marker API...")
                response = requests.post(self.submit_url, headers=headers, files=files, data=data)
                response.raise_for_status()

                # Get request ID
                result = response.json()
                if not result.get('success'):
                    self.logger.error(f"Error: {result.get('error', 'Unknown error')}")
                    return None

                request_id = result['request_id']
                check_url = f"https://www.datalab.to/api/v1/marker/{request_id}"

                # Poll for results
                self.logger.info(f"Processing request {request_id}...")
                max_attempts = 100
                for attempt in range(max_attempts):
                    status_response = requests.get(check_url, headers=headers)
                    status_response.raise_for_status()
                    status = status_response.json()

                    if status.get('status') == 'complete':
                        # Get the markdown content
                        markdown_content = status.get('markdown', '')

                        # Save the markdown content
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(markdown_content)

                        self.logger.info(f"Successfully converted {pdf_path} to {output_path}")
                        return output_path

                    elif status.get('status') == 'error':
                        self.logger.error(f"Error processing PDF: {status.get('error')}")
                        return None

                    # Wait before polling again
                    time.sleep(0.5)

                self.logger.warning("Maximum polling attempts reached. Request may still be processing.")
                return None

        except Exception as e:
            self.logger.error(f"Error converting PDF to markdown: {e}")
            return None

    async def convert_documents(self, pdf_paths: Dict[str, str]) -> Dict[str, str]:
        """
        Convert multiple PDFs to markdown in parallel

        Args:
            pdf_paths: Dictionary mapping document IDs to PDF file paths

        Returns:
            Dictionary mapping document IDs to markdown file paths
        """
        import asyncio

        markdown_paths = {}
        tasks = []

        for doc_id, pdf_path in pdf_paths.items():
            tasks.append(self.convert_to_markdown(pdf_path))

        # Execute conversions in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, (doc_id, _) in enumerate(pdf_paths.items()):
            result = results[i]
            if isinstance(result, Exception):
                self.logger.error(f"Failed to convert PDF for {doc_id}: {result}")
            elif result:
                markdown_paths[doc_id] = result

        return markdown_paths
