import os
import asyncio
import logging
from datetime import datetime


from tender_repository import TenderRepository
from document_retrieval_service import DocumentRetrievalService
from document_conversion_service import DocumentConversionService
from storage_service import StorageService
from ai_document_generator_service import AIDocumentGeneratorService
from ai_documents_processing_workflow import AIDocumentsProcessingWorkflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)
logger = logging.getLogger(__name__)

async def main():
    # Load environment variables
    marker_api_key = os.getenv("MARKER_API", "VE2rjbBG2PS4_XBVrjIwJb1spnflusuWbwGsO9RkbKo")
    print(f"Marker API is: {marker_api_key}")
    google_ai_api_key = os.getenv("GOOGLE_AI_API", "AIzaSyCPaAqSyedsedLml8FtA_mQDZnvA5w0Uo8")

    # Check if keys are available
    if not marker_api_key:
        logger.error("MARKER_API environment variable not set")
        return
    if not google_ai_api_key:
        logger.error("GOOGLE_AI_API environment variable not set")
        return

    # Initialize services
    tender_repo = TenderRepository()
    doc_retrieval = DocumentRetrievalService(output_dir="data/raw_pdfs")
    doc_conversion = DocumentConversionService(api_key=marker_api_key, output_dir="data/markdown")
    storage = StorageService(base_path="data/storage")
    ai_generator = AIDocumentGeneratorService(api_key=google_ai_api_key, model_name="models/gemini-1.5-flash-001")

    # Initialize workflow orchestrator
    workflow = AIDocumentsProcessingWorkflow(
        tender_repository=tender_repo,
        document_retrieval_service=doc_retrieval,
        document_conversion_service=doc_conversion,
        storage_service=storage,
        ai_document_generator_service=ai_generator,
        logger=logger
    )

    # Example usage: process a tender
    tender_id = "10/2024/CONM-CEE"
    client_id = "client123"

    # Setup sample tender data for testing
    tender_repo._tenders[tender_id] = {
        'id': tender_id,
        'document_urls': {
            'doc1': "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?DocumentIdParam=cGvQdaF/qmEnKvN211kkZep9eLYPa5sPlu0VFp1fA/h5Fg1pTaKl4FN73msJksylIVq1IvdI5PofzpP36PwDr6Jmx2BDu2S/t4P9dvlPFULfdyQgZAdTm3EfcUAC7CJ6&cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D",
            'doc2': "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?DocumentIdParam=z/ghU5864J3UKnVAwwWNrCp9Nvi9o32DrO2HfqSQ/7y0QPTDGl%2BTgSxAzGaBF9hR0w94oIWtN2EkYA0Og4DmgZLmV7aY3ZdlQ8%2BxtPvjDpeB0nvVKRzfe4rpHcnlPhSZ&cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D",
            'doc3': "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?DocumentIdParam=8hgVPRbuSgXhyguKtFy5AiXeHvokF%2B2dllmtzd8sapWTAcvE3IDVxGhRuhi9GWXq2A4V3aEdzAqu7KG6zJkIGd4Rr6XPeaqztAIX1SSQM%2B2B0nvVKRzfe4rpHcnlPhSZ&cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D",
            'doc4': "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?DocumentIdParam=wpL05Sv0vuASNVV59os02t1zLXzhEwhUpVrAmIiI4w%2B06WPE0AvLvdg6w0OZqYyrGivKjCsC2R7gEgBRON2aZeZ1y1C5nSiBmcFaXawL1GJt/o8fNevwsujgRzaBbugn&cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D",
            'doc5': "https://contrataciondelestado.es/FileSystem/servlet/GetDocumentByIdServlet?DocumentIdParam=FfZj3XI6OlOTOzDyKek0lnaI3ORlarheXliAsx0JVVCd5gsL7ycTWihmq01TkQC8e9oC1wwahAymbwR1EgIyQ86irt%2BO9F0D/Qe6kMPxUA%2B1aXEvq3KHa/AEHgtDrQw0&cifrado=QUC1GjXXSiLkydRHJBmbpw%3D%3D"
        },
        'markdown_paths': {},
        'ai_summary': None,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }

    # Process the tender
    custom_questions = [
        """
PLANTILLA DE RESUMEN DE INFORMACIÓN PARA LICITACIONES PÚBLICAS
1. INFORMACIÓN GENERAL DEL PROYECTO
Nombre del proyecto: [Nombre completo de la licitación]
Código o referencia de licitación: [Código de identificación]
Entidad convocante: [Organismo que publica la licitación]
Objeto de la licitación: [Descripción breve del servicio/producto a contratar]
Plazo de presentación de ofertas: [Fecha límite de presentación]
""",
        """
2. ASPECTOS ECONÓMICOS Y FINANCIEROS
Solvencia Económica y Financiera
Requisitos básicos: [Especificar si se exige solvencia económica y financiera o si está eximida]
Documentación necesaria: [Declaraciones, certificados u otros documentos requeridos]
Otros comentarios relevantes: [Ejemplo: Se requiere/no se requiere garantía provisional o definitiva]
Presupuesto Base de Licitación
Importe total: [Monto total, especificando si incluye impuestos]
Condiciones económicas: [Forma de distribución del presupuesto]
Desglose por lotes:
Lote 1: [Descripción + Importe]
Lote 2: [Descripción + Importe]
Modificaciones presupuestarias: [Condiciones bajo las cuales se puede modificar el presupuesto]
Garantía Definitiva
Importe de la garantía: [Monto requerido o exención]
Condiciones de devolución: [Si aplica]
Documentación requerida: [Si aplica]
"""
    ]

    result = await workflow.process_tender(tender_id, client_id, regenerate=True, questions=custom_questions)

    # Print the results
    logger.info("=== Processing Results ===")
    logger.info(f"AI Summary generated: {bool(result.get('ai_summary'))}")
    logger.info(f"AI Document generated: {bool(result.get('ai_doc_path'))}")
    logger.info(f"Processing time: {result.get('processing_time', 0):.2f} seconds")

    # Sample of the AI summary
    if result.get('ai_summary'):
        logger.info("\nAI Summary Sample (first 200 chars):")
        logger.info(result['ai_summary'][:200] + "...")

    if result.get('ai_doc_path'):
        logger.info("\nAI Document Sample (first 200 chars):")
        logger.info(result['ai_doc_path'][:200] + "...")

if __name__ == "__main__":
    asyncio.run(main())
