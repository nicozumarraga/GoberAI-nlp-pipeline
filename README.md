# AI Tender Processing Pipeline

An end-to-end pipeline for processing tender documents that extracts structured information from PDFs and generates AI-powered summaries with traceable references to source documents.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export MARKER_API_KEY=your_marker_api_key
export GEMINI_API_KEY=your_gemini_api_key

# Run the pipeline
python chunked_ai_summary_generator.py
```

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ DocumentRetrieval│───▶│ DocumentConversion│───▶│ MarkdownChunking│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ ReferenceProcess│◀───│ AIDocGeneration │◀───│ ChunkAggregation│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

1. **AIDocumentsProcessingWorkflow**: Main orchestrator class that coordinates the pipeline
   - **Input**: `tender_id`, `client_id`, optional custom `questions`
   - **Output**: Paths to generated documents and metadata

2. **DocumentRetrievalService**: Downloads PDFs from URLs
   - Uses async requests for parallel downloads
   - Caches downloads to prevent duplicate retrievals

3. **DocumentConversionService**: Converts PDFs to markdown
   - Uses Marker API for PDF-to-markdown conversion
   - Handles rate limiting and retries

4. **MarkdownChunkingService**: Processes markdown into hierarchical chunks
   - Segments documents based on header structure
   - Preserves original PDF page references and metadata

5. **AIDocumentGeneratorService**: Generates AI documents with chunk references
   - Leverages Gemini API for context-aware generation
   - Implements parallel processing for sections to improve throughput
   - Enforces reference format: `[chunk_id: chunk_documentID,página,sección]`

6. **ChunkReferenceUtility**: Processes chunk references for traceability
   - Converts references to clickable links
   - Generates metadata for UI integration

7. **TenderRepository**: Data access layer (currently mock implementation)
   - Abstracts storage operations for tender data
   - Prepared for future database integration

## Output Files & Directories

The pipeline generates multiple files during processing:

### Directory Structure

```
data/
├── raw_pdfs/                            # Downloaded original PDFs
│   └── DOC20241111091415.pdf            # Format: original filename or timestamp-based name
│
├── markdown/                            # Converted markdown documents
│   └── DOC20241111091415.md             # Same base name as PDF
│
├── chunks/                              # Document chunks
│   └── TENDER_ID/                       # Organized by tender ID
│       ├── doc1_chunks.json             # Hierarchical chunks for a document
│       ├── doc2_chunks.json
│       └── combined_chunks.json         # Flattened list of all chunks
│
└── client_docs/                         # Generated output documents
    └── CLIENT_ID_TENDER_ID_TIMESTAMP.md # AI-generated document
    └── CLIENT_ID_TENDER_ID_TIMESTAMP_processed.md # Document with processed references
    └── CLIENT_ID_TENDER_ID_TIMESTAMP_references.json # Reference metadata
```

### Key Output Files

1. **PDF Documents** (`data/raw_pdfs/*.pdf`)
   - Original downloaded tender documents
   - Preserved for traceability and reference

2. **Markdown Files** (`data/markdown/*.md`)
   - Converted text content from PDFs
   - Include page markers: `{PAGE_NUMBER}------------------------------------------------`
   - Used as input for chunking

3. **Chunk Files** (`data/chunks/TENDER_ID/*.json`)
   - **Document Chunks** (`doc*_chunks.json`):
     ```json
     {
       "text": "Full document text",
       "metadata": {
         "chunk_id": "chunk_0_document",
         "level": 0,
         "title": "Document Title",
         "parent_id": null,
         "pdf_path": "data/raw_pdfs/document.pdf",
         "page_number": 1,
         "start_line": 1,
         "end_line": 100
       },
       "children": [
         {
           "text": "Section text",
           "metadata": {...},
           "children": [...]
         }
       ]
     }
     ```

   - **Combined Chunks** (`combined_chunks.json`):
     ```json
     [
       {
         "chunk_id": "chunk_0_document",
         "level": 0,
         "title": "Document Title",
         "text": "Full document text",
         "parent_id": null,
         "pdf_path": "data/raw_pdfs/document.pdf",
         "page_number": 1,
         "start_line": 1,
         "end_line": 100
       },
       {...}
     ]
     ```

4. **AI Document** (`data/client_docs/CLIENT_ID_TENDER_ID_TIMESTAMP.md`)
   - AI-generated summary with section-based responses to prompts
   - Contains references to chunks: `[chunk_id: chunk_0_1_section_name]`
   - Format:
     ```markdown
     # AI Summary for Tender T12345

     ## 1. ¿Cuál es el objeto de la licitación?

     El objeto de la licitación es [...] [chunk_id: chunk_0_1_objeto]

     ## 2. ¿Cuáles son los requisitos técnicos principales?
     [...]
     ```

5. **Processed Document** (`data/client_docs/CLIENT_ID_TENDER_ID_TIMESTAMP_processed.md`)
   - Same content as AI Document but with references converted to clickable links
   - References appear as: `[📄](path/to/pdf#page=5 "Document Title, Page 5")`
   - Used for display in frontend applications

6. **Reference Metadata** (`data/client_docs/CLIENT_ID_TENDER_ID_TIMESTAMP_references.json`)
   - Maps references to their source documents and pages
   - Used by frontend for interactive features
   - Format:
     ```json
     {
       "references": [
         {
           "reference_id": "ref_1",
           "chunk_id": "chunk_0_1_objeto",
           "position": {
             "start": 120,
             "end": 150
           },
           "source": {
             "pdf_path": "data/raw_pdfs/document.pdf",
             "page_number": 5,
             "title": "Document Title"
           }
         }
       ]
     }
     ```

## Technical Implementation

### Data Structures

#### Chunk Metadata
```python
@dataclass
class ChunkMetadata:
    chunk_id: str         # Unique identifier
    level: int            # Hierarchical level (0=doc, 1=section...)
    title: str            # Title from header
    parent_id: str        # Parent chunk ID
    pdf_path: str         # Path to source PDF
    page_number: int      # Page in source PDF
    start_line: int       # Start line in markdown
    end_line: int         # End line in markdown
```

#### Document Chunk
```python
@dataclass
class DocumentChunk:
    text: str
    metadata: ChunkMetadata
    children: List["DocumentChunk"] = None
```

### API Integration

#### Marker API (PDF Conversion)
- Content types: PDF, DOCX
- Response includes markdown content, pagination and status

#### Gemini API (AI Generation)
- Model: gemini-2.0-flash-lite
- Response includes generated text

## Usage Examples

### 1. Basic Pipeline

```python
from ai_documents_processing_workflow import AIDocumentsProcessingWorkflow
import asyncio
import os

# Initialize components (see detailed example below)
# ...

async def process_single_tender():
    result = await workflow.process_tender(
        tender_id="T12345",
        client_id="C6789",
        regenerate=True
    )
    return result

# Run the async function
asyncio.run(process_single_tender())
```

### 2. Complete Implementation

```python
import os
import logging
import asyncio
from ai_documents_processing_workflow import AIDocumentsProcessingWorkflow
from tender_repository import TenderRepository
from document_retrieval_service import DocumentRetrievalService
from document_conversion_service import DocumentConversionService
from storage_service import StorageService
from ai_document_generator_service import AIDocumentGeneratorService
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("tender_pipeline")

# Initialize components
tender_repository = TenderRepository()
document_retrieval_service = DocumentRetrievalService(
    output_dir="data/raw_pdfs"
)
document_conversion_service = DocumentConversionService(
    api_key=os.getenv("MARKER_API_KEY"),
    output_dir="data/markdown"
)
storage_service = StorageService()
ai_document_generator_service = AIDocumentGeneratorService(
    api_key=os.getenv("GEMINI_API_KEY"),
    model_name="models/gemini-2.0-flash-lite"
)

# Initialize workflow
workflow = AIDocumentsProcessingWorkflow(
    tender_repository=tender_repository,
    document_retrieval_service=document_retrieval_service,
    document_conversion_service=document_conversion_service,
    storage_service=storage_service,
    ai_document_generator_service=ai_document_generator_service,
    logger=logger
)

# Define custom questions
questions = [
    """
    1. ¿Cuál es el objeto de la licitación?
    2. ¿Cuáles son los requisitos técnicos principales?
    3. ¿Cuál es el presupuesto y la forma de pago?
    """,
    """
    4. ¿Cuáles son los criterios de adjudicación?
    5. ¿Cuáles son los plazos clave?
    """
]

# Document URLs to process
document_urls = {
    "doc1": "https://example.com/path/to/tender.pdf",
    "doc2": "https://example.com/path/to/technical_specs.pdf",
}

async def process_tender():
    # Create or update the tender with document URLs
    tender_repository.create_or_update_tender(
        tender_id="T12345",
        document_urls=document_urls
    )

    # Process the tender
    result = await workflow.process_tender(
        tender_id="T12345",
        client_id="C6789",
        regenerate=True,
        questions=questions
    )

    return result

if __name__ == "__main__":
    result = asyncio.run(process_tender())

    # Print results
    print(f"AI document: {result['ai_doc_path']}")
    print(f"Chunks: {result['chunks_path']}")
    print(f"Processed document: {result['processed_doc_path']}")
    print(f"Reference metadata: {result['reference_metadata_path']}")
    print(f"Processing time: {result['processing_time']:.2f} seconds")
```

## Project Structure

```
clean_ai_tender_summaries/
├── ai_documents_processing_workflow.py  # Main orchestrator
├── document_retrieval_service.py        # PDF retrieval
├── document_conversion_service.py       # PDF to markdown conversion
├── markdown_chunking_service.py         # Hierarchical chunking
├── ai_document_generator_service.py     # AI document generation
├── chunk_reference_utility.py           # Reference processing
├── tender_repository.py                 # Data management
├── storage_service.py                   # File storage
├── chunked_ai_summary_generator.py      # Pipeline runner
└── data/                                # Storage directory
    ├── raw_pdfs/                        # Downloaded PDFs
    ├── markdown/                        # Converted markdown
    ├── chunks/                          # Chunk JSONs
    └── client_docs/                     # Generated documents
```

## Performance Considerations

- **Memory Usage**: Large PDFs can consume significant memory during conversion
  - Recommended server: 4+ GB RAM for production use

- **Processing Time**:
  - PDF Download: ~1-5s per document
  - PDF Conversion: ~5-20s per document (depends on size)
  - Chunking: ~1-3s per document
  - AI Generation: ~6-13s per section

- **Concurrency**:
  - PDF downloads: Parallel (async)
  - PDF conversion: Parallel (async)
  - AI generation: Sections processed in parallel
  - Rate limiting applied to API calls

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `ConnectionError` | Network issues when downloading PDFs | Check connectivity, increase timeout in `document_retrieval_service.py` |
| `APIKeyError` | Invalid Marker/Gemini API key | Verify API keys in `.env` file |
| `ConversionError` | PDF conversion failed | Check PDF format, try with smaller documents first |
| `ChunkingError` | Markdown parsing issues | Verify markdown format, check log for specific parsing errors |
| `GenerationError` | AI model error | Check model availability, reduce question complexity, try smaller batch sizes |

## Development Guidelines

1. **Error Handling**: Always wrap API calls in try-except blocks
2. **Logging**: Use the provided logger for consistent logging
3. **Testing**: Run `chunked_ai_summary_generator.py` to verify chunking functionality
4. **Branching**: Use feature branches, merge to main with PR

---

*Internal documentation - confidential*
