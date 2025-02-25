import os
import pathlib
import requests
import time
from typing import Optional, List
from config import test_config

from google import genai
from google.genai import types

class GeminiRAG():
    def __init__(
        self,
        model_name: str = 'models/gemini-1.5-flash-001',
        api_key: Optional[str] = None,
        cache_ttl: str = "360s"  # 1 hour cache
    ):
        self.api_key = api_key or test_config.GOOGLE_AI_API

        if not self.api_key:
            raise ValueError("API key not found. Please set env variable")

        self.model_name = model_name
        self.cache_ttl = cache_ttl
        self.client = genai.Client(api_key=self.api_key)

    def process_pdf_documents(self, file_paths: List[str], cache_name: str = "tender_documents"):
        """Upload and process documents, create cache"""
        # Upload all documents
        uploaded_files = []
        for file_path in file_paths:
            print(f"Processing {file_path}...")
            doc_file = self.client.files.upload(file=pathlib.Path(file_path))

            # Wait for processing
            while doc_file.state.name == 'PROCESSING':
                print('Waiting for document to be processed...')
                time.sleep(2)
                doc_file = self.client.files.get(name=doc_file.name)

            uploaded_files.append(doc_file)
            print(f'Document processed: {doc_file.uri}')

        # Create cache
        cache = self.client.caches.create(
            model=self.model_name,
            config=types.CreateCachedContentConfig(
                display_name=cache_name,
                system_instruction=(
                    'Eres un asistente experto en licitaciones públicas españolas. '
                    'Responde basándote en los documentos proporcionados.'
                ),
                contents=uploaded_files,
                ttl=self.cache_ttl,
            )
        )

        return cache

    def process_mkd_documents(self, file_paths: List[str], cache_name: str = "tender_documents"):
        """Upload and process markdown documents, create cache"""
        # Upload all documents
        uploaded_files = []
        for file_path in file_paths:
            print(f"Processing {file_path}...")

            # Read markdown content
            try:

                # Upload the file
                doc_file = self.client.files.upload(file=pathlib.Path(file_path),
                                                    config=dict(mime_type='text/markdown'))

                # Wait for processing
                while doc_file.state.name == 'PROCESSING':
                    print('Waiting for document to be processed...')
                    time.sleep(2)
                    doc_file = self.client.files.get(name=doc_file.name)

                uploaded_files.append(doc_file)
                print(f'Document processed: {doc_file.uri}')

            except Exception as e:
                print(f"Error processing markdown file {file_path}: {e}")
                continue

        if not uploaded_files:
            raise ValueError("No documents were successfully processed")

        # Create cache
        cache = self.client.caches.create(
            model=self.model_name,
            config=types.CreateCachedContentConfig(
                display_name=cache_name,
                system_instruction=(
                    'Eres un asistente experto en licitaciones públicas españolas. '
                    'Responde basándote en los documentos proporcionados.'
                ),
                contents=uploaded_files,
                ttl=self.cache_ttl,
            )
        )

        return cache

    def query(self, cache, question: str):
        """Query documents using the cache"""

        prompt = f"""Por favor, busca en los documentos proporcionados y completa de manera especifica y detallada la siguiente plantilla.

Plantilla: {question}

IMPORTANTE: Responde siempre con la información extraida del texto, asume que el usuario final no tiene acceso al documento y
debemos darle toda la información necesaria en nuestra respuesta. Cita textualmente el texto
Nunca respondas con "se especifica en el apartado...", siempre responde con la información final.

"""

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=question,
            config=types.GenerateContentConfig(cached_content=cache.name)
        )

        print("\nToken Usage:")
        print(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
        print(f"Cached content tokens: {response.usage_metadata.cached_content_token_count}")
        print(f"Response tokens: {response.usage_metadata.candidates_token_count}")
        print(f"Total tokens: {response.usage_metadata.total_token_count}")

        return response.text
