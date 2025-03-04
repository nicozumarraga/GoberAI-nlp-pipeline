import os
import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

class AIDocumentsProcessingWorkflow:
    """
    Orchestrator for the AI document processing workflow.
    Coordinates the parallel steps, handles concurrency, and aggregates results.
    """

    def __init__(
        self,
        tender_repository,
        document_retrieval_service,
        document_conversion_service,
        storage_service,
        ai_document_generator_service,
        logger=None
    ):
        self.tender_repository = tender_repository
        self.document_retrieval_service = document_retrieval_service
        self.document_conversion_service = document_conversion_service
        self.storage_service = storage_service
        self.ai_document_generator_service = ai_document_generator_service
        self.logger = logger or logging.getLogger(__name__)

    async def process_tender(
        self,
        tender_id: str,
        client_id: str,
        regenerate: bool = False,
        questions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Process a tender to generate AI summary and client-specific AI document

        Args:
            tender_id: ID of the tender to process
            client_id: ID of the client
            regenerate: Whether to regenerate summaries even if they already exist
            questions: Optional list of questions/sections to use for the AI document

        Returns:
            Dictionary with AI summary and AI document
        """
        start_time = datetime.now()
        self.logger.info(f"Starting tender processing for tender_id={tender_id}, client_id={client_id}")

        # 1. Retrieve Tender and ClientTender information
        tender = self.tender_repository.get_tender_by_id(tender_id)
        client_tender = self.tender_repository.get_client_tender(tender_id, client_id)

        # Check if we need to generate AI docs or can return existing ones
        if not regenerate and tender.get('ai_summary') and client_tender.get('ai_doc_path'):
            self.logger.info("Using existing AI documents")
            # Calculate processing time
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            return {
                'ai_summary': tender['ai_summary'],
                'ai_doc_path': client_tender['ai_doc_path'],
                'regenerated': False,
                'processing_time': processing_time
            }

        # 2. Identify missing Markdown files
        document_urls = tender.get('document_urls', {})
        markdown_paths = tender.get('markdown_paths', {})

        missing_docs = {}
        for doc_id, url in document_urls.items():
            if doc_id not in markdown_paths or not markdown_paths[doc_id]:
                missing_docs[doc_id] = url

        # 3. Process missing documents in parallel
        new_markdown_paths = {}
        if missing_docs:
            self.logger.info(f"Processing {len(missing_docs)} missing documents")

            # 3a. Download PDFs
            pdf_paths = await self.document_retrieval_service.retrieve_documents(missing_docs)

            # 3b. Convert to Markdown
            if pdf_paths:
                new_md_paths = await self.document_conversion_service.convert_documents(pdf_paths)
                new_markdown_paths.update(new_md_paths)

            # 3c. Update Tender with new Markdown paths
            if new_markdown_paths:
                tender = self.tender_repository.update_markdown_paths(tender_id, new_markdown_paths)

        # 4. Prepare the complete list of Markdown paths
        all_markdown_paths = list(tender['markdown_paths'].values())
        if not all_markdown_paths:
            raise ValueError(f"No markdown documents available for tender {tender_id}")

        # 5. Generate client-specific AI document
        ai_doc_path = client_tender.get('ai_doc_path')
        if regenerate or not ai_doc_path:
            # Use provided questions or default questions
            doc_questions = questions or [
                "1. ¿Cuál es el objeto de la licitación?",
                "2. ¿Cuáles son los requisitos técnicos principales?",
                "3. ¿Cuál es el presupuesto y la forma de pago?",
                "4. ¿Cuáles son los criterios de adjudicación?",
                "5. ¿Cuáles son los plazos clave?"
            ]

            # Generate output filename for storing results
            timestamp = int(datetime.now().timestamp())
            output_dir = "data/client_docs"
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, f"{client_id}_{tender_id}_{timestamp}.md")

            # Generate the AI document and get the path
            ai_doc_path = await self.ai_document_generator_service.generate_ai_documents(
                all_markdown_paths, doc_questions, output_file
            )

            if ai_doc_path:
                client_tender = self.tender_repository.update_ai_doc(tender_id, client_id, ai_doc_path)
            else:
                self.logger.error(f"Failed to generate AI document for client {client_id}, tender {tender_id}")
                # If AI document generation failed, we can't continue with summary generation
                end_time = datetime.now()
                processing_time = (end_time - start_time).total_seconds()
                return {
                    'ai_summary': None,
                    'ai_doc_path': None,
                    'regenerated': True,
                    'processing_time': processing_time
                }

        # 6. Generate AI summary based on the AI document
        if regenerate or not tender.get('ai_summary'):
            # Read the AI document
            try:
                with open(client_tender.get('ai_doc_path'), 'r', encoding='utf-8') as f:
                    ai_doc_content = f.read()

                # Now generate summary using the AI document as context
                ai_summary = await self.ai_document_generator_service.generate_conversational_summary(
                    ai_doc_content, tender_id
                )

                if ai_summary:
                    tender = self.tender_repository.update_ai_summary(tender_id, ai_summary)
                else:
                    self.logger.error(f"Failed to generate AI summary for tender {tender_id}")
            except Exception as e:
                self.logger.error(f"Error reading AI document or generating summary: {e}")

        # Calculate final processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        self.logger.info(f"Tender processing completed in {processing_time:.2f} seconds")

        # Update the return value to include paths
        return {
            'ai_summary': tender.get('ai_summary'),
            'ai_doc_path': client_tender.get('ai_doc_path'),
            'regenerated': regenerate or not tender.get('ai_summary') or not ai_doc_path,
            'processing_time': processing_time
        }
