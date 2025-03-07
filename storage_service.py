import os
import logging
from typing import Optional

class StorageService:
    """Service for storing and retrieving files from storage (S3, local, etc.)"""

    def __init__(self, base_path: str = "data/storage"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    async def upload_markdown(self, markdown_content: str, key: str) -> Optional[str]:
        """
        Upload markdown content to storage

        Args:
            markdown_content: The markdown text to upload
            key: The storage key (path) to use

        Returns:
            The storage URL/path if successful, None otherwise
        """
        try:
            # Ensure path exists
            file_path = os.path.join(self.base_path, key)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Write the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            self.logger.info(f"Uploaded markdown to {file_path}")
            return file_path

        except Exception as e:
            self.logger.error(f"Error uploading markdown: {e}")
            return None

    async def get_markdown(self, key: str) -> Optional[str]:
        """
        Retrieve markdown content from storage

        Args:
            key: The storage key (path) to retrieve

        Returns:
            The markdown content if found, None otherwise
        """
        try:
            file_path = os.path.join(self.base_path, key)

            if not os.path.exists(file_path):
                self.logger.warning(f"File not found: {file_path}")
                return None

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            self.logger.info(f"Retrieved markdown from {file_path}")
            return content

        except Exception as e:
            self.logger.error(f"Error retrieving markdown: {e}")
            return None
