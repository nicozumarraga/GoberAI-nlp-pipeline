import logging
import time
import random
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

from google import genai
from google.genai import types

class AIDocumentGeneratorService:
    """Service for generating AI-based document summaries using Gemini"""

    def __init__(
        self,
        api_key: str,
        model_name: str = 'models/gemini-1.5-flash-001',
        cache_ttl: str = "360s",  # 6 minute cache for testing
        min_token_count: int = 32768  # Minimum tokens needed for caching
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.cache_ttl = cache_ttl
        self.min_token_count = min_token_count
        self.logger = logging.getLogger(__name__)

        # Initialize the Gemini client
        self.client = genai.Client(api_key=api_key)

    def _calculate_tokens(self, text: str) -> int:
        """Rough estimation of token count (actual tokenization is more complex)"""
        # Very rough approximation: ~4 chars per token for English text
        return len(text) // 4

    def process_markdown_documents(
        self,
        markdown_paths: List[str],
        cache_name: str = "tender_documents"
    ) -> Dict[str, Any]:
        """
        Upload and process markdown documents to create a query cache

        Args:
            markdown_paths: List of paths to markdown files
            cache_name: Name for the document cache

        Returns:
            Dictionary with cache information and document contents for direct use
        """
        # Upload all documents
        uploaded_files = []
        total_tokens = 0
        document_contents = []

        for file_path in markdown_paths:
            self.logger.info(f"Processing {file_path}...")

            try:
                # Read the file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Store content for direct use if needed
                    document_contents.append({
                        "path": file_path,
                        "content": content
                    })

                # Roughly estimate token count
                file_tokens = self._calculate_tokens(content)
                total_tokens += file_tokens

                # Upload the file
                doc_file = self.client.files.upload(
                    file=Path(file_path),
                    config=dict(mime_type='text/markdown')
                )

                # Wait for processing
                while doc_file.state.name == 'PROCESSING':
                    self.logger.info('Waiting for document to be processed...')
                    time.sleep(2)
                    doc_file = self.client.files.get(name=doc_file.name)

                uploaded_files.append(doc_file)
                self.logger.info(f'Document processed: {doc_file.uri}')

            except Exception as e:
                self.logger.error(f"Error processing markdown file {file_path}: {e}")
                continue

        if not uploaded_files:
            raise ValueError("No documents were successfully processed")

        # Check if total tokens meet minimum requirement
        if total_tokens < self.min_token_count:
            self.logger.warning(
                f"Total tokens ({total_tokens}) is below minimum required for caching "
                f"({self.min_token_count}). Will process without caching."
            )
            return {
                "files": uploaded_files,
                "use_cache": False,
                "total_tokens": total_tokens,
                "document_contents": document_contents
            }

        # Create cache
        try:
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
            return {
                "cache": cache,
                "use_cache": True,
                "total_tokens": total_tokens,
                "document_contents": document_contents
            }
        except Exception as e:
            self.logger.error(f"Error creating cache: {e}")
            return {
                "files": uploaded_files,
                "use_cache": False,
                "total_tokens": total_tokens,
                "document_contents": document_contents
            }

    def _build_system_prompt_with_documents(self, document_contents: List[Dict[str, str]]) -> str:
        """
        Build a system prompt that includes relevant document content

        Args:
            document_contents: List of dictionaries with document path and content

        Returns:
            System prompt with embedded document content
        """
        system_prompt = "Eres un asistente experto en licitaciones públicas españolas. Aquí están los documentos relevantes:\n\n"

        for i, doc in enumerate(document_contents):
            # Extract filename from path for better context
            filename = os.path.basename(doc["path"])

            # Include the full document content without truncation
            system_prompt += f"--- DOCUMENTO {i+1}: {filename} ---\n{doc['content']}\n\n"

        system_prompt += "Analiza estos documentos y proporciona información precisa basándote en ellos."
        return system_prompt

    def estimate_total_tokens(self, markdown_paths: List[str]) -> int:
        """
        Estimate the total token count from markdown files without API calls

        Args:
            markdown_paths: List of paths to markdown files

        Returns:
            Estimated total token count
        """
        total_tokens = 0

        for path in markdown_paths:
            try:
                # Read the file content
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Roughly estimate token count
                file_tokens = self._calculate_tokens(content)
                total_tokens += file_tokens

                self.logger.debug(f"Estimated tokens for {path}: {file_tokens}")

            except Exception as e:
                self.logger.error(f"Error estimating tokens for {path}: {e}")
                continue

        self.logger.info(f"Total estimated tokens: {total_tokens}")
        return total_tokens

    async def generate_ai_documents(
        self,
        markdown_paths: List[str],
        questions: List[str],
        output_file: str,
        max_retries: int = 5
    ) -> Optional[str]:
        """
        Generate client-specific AI documents by processing questions sequentially

        Args:
            markdown_paths: List of paths to markdown files
            questions: List of questions/sections to process
            output_file: File to write the results to
            max_retries: Maximum number of retries for API calls

        Returns:
            Path to the generated document if successful, None otherwise
        """
        self.logger.info("Generating AI documents sequentially...")

        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        os.makedirs(output_dir, exist_ok=True)

        # Create a directory for individual section responses
        sections_dir = os.path.join(output_dir, "sections")
        os.makedirs(sections_dir, exist_ok=True)

        # Estimate token count before processing
        estimated_tokens = self.estimate_total_tokens(markdown_paths)

        # Check if total tokens meet minimum requirement for caching
        use_cache = estimated_tokens >= self.min_token_count
        cache_result = {"use_cache": use_cache}

        if use_cache:
            # Only process documents if we'll be using caching
            self.logger.info(f"Estimated tokens ({estimated_tokens}) exceed minimum for caching. Processing documents...")

            # Process documents
            cache_result = await self.process_markdown_documents(markdown_paths)
        else:
            self.logger.warning(
                f"Estimated tokens ({estimated_tokens}) is below minimum required for caching "
                f"({self.min_token_count}). Will process without caching."
            )
            # Add document contents for direct use if needed
            cache_result["document_contents"] = []
            for file_path in markdown_paths:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    cache_result["document_contents"].append({
                        "path": file_path,
                        "content": content
                    })
                except Exception as e:
                    self.logger.error(f"Error reading markdown file {file_path}: {e}")

        # Prepare system prompt if not using cache
        system_prompt = None
        if not cache_result.get("use_cache", False):
            system_prompt = self._build_system_prompt_with_documents(
                cache_result.get("document_contents", [])
            )

        full_response = ""
        accumulated_context = ""
        section_files = []

        for i, question in enumerate(questions):
            section_start_time = time.time()
            section_number = i + 1
            self.logger.info(f"Processing section {section_number}/{len(questions)}: {question[:50]}...")

            # Build a prompt that incorporates previous context
            if accumulated_context:
                prompt = f"""Por favor, busca en los documentos proporcionados y completa de manera
                específica y detallada la siguiente plantilla.

                Plantilla: {question}

                IMPORTANTE:
                1. Continúa donde lo dejaste sin repetir información.
                2. Responde siempre con la información extraida del texto
                3. Asume que el usuario final no tiene acceso al documento
                4. Cita textualmente el texto cuando sea relevante
                5. Nunca respondas con "se especifica en el apartado...", siempre responde con la información final
                """
            else:
                # First question, no context yet
                prompt = f"""Por favor, busca en los documentos proporcionados y completa de manera
                específica y detallada la siguiente plantilla.

                Plantilla: {question}

                IMPORTANTE: Responde siempre con la información extraida del texto, asume que el usuario
                final no tiene acceso al documento y debemos darle toda la información necesaria en nuestra
                respuesta. Cita textualmente el texto cuando sea relevante.
                Nunca respondas con "se especifica en el apartado...", siempre responde con la información final.
                """

            # Process the section with retries
            section_response = await self._process_section_with_retries(
                prompt, system_prompt, cache_result, section_number,
                len(questions), section_start_time, max_retries
            )

            if not section_response:
                self.logger.error(f"Failed to generate section {section_number}")
                continue

            # Save this section to a separate file for logging
            section_file = os.path.join(sections_dir, f"section_{section_number}.md")
            with open(section_file, 'w', encoding='utf-8') as f:
                f.write(section_response)
            section_files.append(section_file)

            self.logger.info(f"Section {section_number} saved to {section_file}")

            # Add to accumulated context and full response
            accumulated_context += section_response
            full_response += section_response + "\n\n"

        # Only write the final document if we have content
        if full_response:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(full_response)
            self.logger.info(f"Complete AI document written to {output_file}")
            return output_file

        return None

    async def _process_section_with_retries(
        self, prompt, system_prompt, cache_result,
        section_number, total_sections, section_start_time, max_retries
    ) -> Optional[str]:
        """Process a single section with retry logic"""
        retry_count = 0
        initial_delay = 1.0
        delay = initial_delay

        while retry_count <= max_retries:
            try:
                if cache_result.get("use_cache", False):
                    # Use cache if available
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=prompt,
                        config=types.GenerateContentConfig(cached_content=cache_result["cache"].name)
                    )
                else:
                    # Fallback to direct query with document content in system prompt
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=[
                            {
                                "role": "user",
                                "parts": [{"text": system_prompt}]
                            },
                            {
                                "role": "user",
                                "parts": [{"text": prompt}]
                            }
                        ]
                    )

                # Log token usage if available
                if hasattr(response, 'usage_metadata'):
                    section_time = time.time() - section_start_time
                    self.logger.info(f"\nSection {section_number} completed in {section_time:.2f} seconds")
                    self.logger.info(f"Token Usage:")
                    self.logger.info(f"  Prompt tokens: {response.usage_metadata.prompt_token_count}")
                    if hasattr(response.usage_metadata, 'cached_content_token_count'):
                        self.logger.info(f"  Cached content tokens: {response.usage_metadata.cached_content_token_count}")
                    self.logger.info(f"  Response tokens: {response.usage_metadata.candidates_token_count}")
                    self.logger.info(f"  Section total: {response.usage_metadata.total_token_count}")

                print(f"AI GENERATED RESPONSE FOR SECTION {section_number}: {response.text}")
                return response.text

            except Exception as e:
                retry_count += 1
                self.logger.error(f"Error processing section {section_number} (attempt {retry_count}/{max_retries}): {e}")

                if retry_count > max_retries:
                    self.logger.error(f"Failed to process section {section_number} after {max_retries} retries")
                    return None

                # Add jitter to avoid thundering herd
                jitter = random.uniform(0.8, 1.2)
                actual_delay = delay * jitter
                self.logger.info(f"Retrying in {actual_delay:.2f} seconds...")
                time.sleep(actual_delay)

                # Exponential backoff
                delay *= 2

        return None

    async def generate_conversational_summary(
        self,
        document_content: str,
        tender_id: str,
        max_retries: int = 3
    ) -> Optional[str]:
        """
        Generate a conversational summary based on the AI document

        Args:
            document_content: Content of the AI document
            tender_id: ID of the tender
            max_retries: Maximum number of retries for API calls

        Returns:
            Conversational summary if successful, None otherwise
        """
        self.logger.info("Generating conversational summary from AI document...")

        prompt = f"""
        Eres un asistente experto en licitaciones públicas. A continuación, te presento un documento detallado
        sobre la licitación {tender_id}.

        {document_content}

        Por favor, genera un resumen breve (máximo 1500 caracteres) en un estilo profesional y
        directo que destaque los puntos más importantes de esta licitación. Incluye el objeto, presupuesto,
        plazos clave y cualquier particularidad que consideres relevante.

        Ejemplo: La licitación 10/2024/CONM-CEE busca un proveedor para el suministro de plantas y decoración
        floral navideña en el centro de Jaén. El proyecto se divide en dos lotes: Suministro de plantas (7.040€ + IVA)
        y servicio de decoración (4.840€ + IVA), con un presupuesto total de 11.880€ + IVA. No se exige solvencia
        económica o técnica y el plazo de presentación de ofertas finaliza el 25/11/2024 a las 14:00. La adjudicación
        se realiza a la oferta económica más baja.  El contrato se extiende hasta fin de 2024 y el adjudicatario debe
        presentar una declaración responsable sobre medidas de igualdad de género en el mercado laboral.  Se deben
        cumplir las normas de protección medioambiental y la normativa vigente en materia laboral.  Los licitadores deben
        revisar los anexos para detalles específicos sobre las plantas, materiales y plazos de entrega.
        """

        # Retry with exponential backoff
        retry_count = 0
        initial_delay = 1.0
        delay = initial_delay

        while retry_count <= max_retries:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[{
                        "role": "user",
                        "parts": [{"text": prompt}]
                    }]
                )

                # Log token usage if available
                if hasattr(response, 'usage_metadata'):
                    self.logger.info("\nToken Usage (Summary):")
                    self.logger.info(f"Prompt tokens: {response.usage_metadata.prompt_token_count}")
                    self.logger.info(f"Response tokens: {response.usage_metadata.candidates_token_count}")
                    self.logger.info(f"Total tokens: {response.usage_metadata.total_token_count}")

                return response.text

            except Exception as e:
                retry_count += 1
                self.logger.error(f"Error generating conversational summary (attempt {retry_count}/{max_retries}): {e}")

                if retry_count > max_retries:
                    self.logger.error(f"Failed to generate conversational summary after {max_retries} retries")
                    return None

                # Add jitter to avoid thundering herd
                jitter = random.uniform(0.8, 1.2)
                actual_delay = delay * jitter
                self.logger.info(f"Retrying in {actual_delay:.2f} seconds...")
                time.sleep(actual_delay)

                # Exponential backoff
                delay *= 2

        return None
