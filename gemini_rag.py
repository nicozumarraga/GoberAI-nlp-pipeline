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
        self.history = []

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

    def query_sequential(self, cache, questions: List[str], output_file: Optional[str] = None, max_retries: int = 5, initial_retry_delay: float = 1.0):
        """
        Process a list of questions sequentially, maintaining context between queries

        Args:
            cache: The document cache to query
            questions: List of questions/sections to process
            output_file: Optional file to write the results to
            max_retries: Maximum number of retries for failed requests
            initial_retry_delay: Initial delay before retrying (seconds), will increase exponentially

        Returns:
            Complete aggregated response
        """
        import time
        import random

        full_response = ""
        accumulated_context = ""
        total_tokens = 0

        for i, question in enumerate(questions):
            section_start_time = time.time()
            print(f"\nProcessing section {i+1}/{len(questions)}: {question[:50]}...")

            # Build a prompt that incorporates previous context
            if accumulated_context:
                prompt = f"""Por favor, continúa completando la plantilla con la siguiente sección.

Lo que ya has respondido anteriormente:
{accumulated_context}

Ahora completa la siguiente sección:
{question}

IMPORTANTE:
1. Continúa donde lo dejaste sin repetir información
2. Responde siempre con la información extraida del texto
3. Asume que el usuario final no tiene acceso al documento
4. Cita textualmente el texto cuando sea relevante
5. Nunca respondas con "se especifica en el apartado...", siempre responde con la información final
"""
            else:
                # First question, no context yet
                prompt = f"""Por favor, busca en los documentos proporcionados y completa de manera especifica y detallada la siguiente plantilla.

Plantilla: {question}

IMPORTANTE: Responde siempre con la información extraida del texto, asume que el usuario final no tiene acceso al documento y
debemos darle toda la información necesaria en nuestra respuesta. Cita textualmente el texto
Nunca respondas con "se especifica en el apartado...", siempre responde con la información final.
"""

            # Generate response with retry logic
            retry_count = 0
            retry_delay = initial_retry_delay
            section_response = None

            while retry_count <= max_retries:
                try:
                    # Generate response
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(cached_content=cache.name)
                    )

                    # Track token usage
                    prompt_tokens = response.usage_metadata.prompt_token_count
                    cached_tokens = response.usage_metadata.cached_content_token_count
                    response_tokens = response.usage_metadata.candidates_token_count
                    section_total = response.usage_metadata.total_token_count
                    total_tokens += section_total

                    # Track timing
                    section_time = time.time() - section_start_time

                    # Print metrics
                    print(f"\nSection {i+1} completed in {section_time:.2f} seconds")
                    print(f"Token Usage:")
                    print(f"  Prompt tokens: {prompt_tokens}")
                    print(f"  Cached content tokens: {cached_tokens}")
                    print(f"  Response tokens: {response_tokens}")
                    print(f"  Section total: {section_total}")
                    print(f"  Running total: {total_tokens}")

                    section_response = response.text
                    break  # Success, exit retry loop

                except Exception as e:
                    retry_count += 1

                    # Check if we've hit the max retries
                    if retry_count > max_retries:
                        raise Exception(f"Failed to process section {i+1} after {max_retries} retries: {str(e)}")

                    # Calculate delay with jitter
                    jitter = random.uniform(0.8, 1.2)
                    actual_delay = retry_delay * jitter

                    # Log retry attempt
                    print(f"Error processing section {i+1}: {str(e)}")
                    print(f"Retrying in {actual_delay:.2f} seconds (attempt {retry_count}/{max_retries})...")

                    # Wait before retrying
                    time.sleep(actual_delay)

                    # Exponential backoff
                    retry_delay *= 2

            # Append to result
            full_response += section_response + "\n\n"

            # Update the accumulated context
            accumulated_context += section_response

            # Optionally write to file as we go (in case of interruptions)
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(full_response)

        return full_response
