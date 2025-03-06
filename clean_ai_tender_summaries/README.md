# Hierarchical Markdown Chunking for AI Document Processing

This system provides hierarchical chunking capabilities for markdown documents, with a focus on preserving references to original PDF sources. The chunks are labeled in a way that allows LLMs to reference specific chunks in their answers, and these references can be mapped in the frontend to the original PDF sources.

## Features

- Hierarchical chunking of markdown documents based on header structure
- Preservation of metadata including PDF source and page numbers
- Utility functions for handling chunk references in AI-generated documents
- Ability to replace references with clickable links to original PDFs
- Support for generating reference metadata for use in UIs

## Components

1. **MarkdownChunkingService**: Processes markdown documents into hierarchical chunks
2. **ChunkReferenceUtility**: Handles chunk references in AI-generated documents
3. **AIDocumentsProcessingWorkflow**: Orchestrates the chunking process within the larger AI document generation workflow
4. **AIDocumentGeneratorService**: Generates AI documents with chunk references

## Installation

Ensure you have Python 3.7+ installed, then install the required dependencies:

```bash
pip install requests google-generativeai
```

## Usage

### 1. Testing the Chunking Process

To test the chunking process on a markdown file:

```bash
python test_markdown_chunking.py --markdown path/to/markdown.md --pdf path/to/source.pdf
```

This will:
1. Chunk the markdown file
2. Create a sample document with references
3. Process the references in the sample document

### 2. Running the Complete Pipeline

The AI documents processing workflow handles the complete process:

```python
from ai_documents_processing_workflow import AIDocumentsProcessingWorkflow
from tender_repository import TenderRepository
from document_retrieval_service import DocumentRetrievalService
from document_conversion_service import DocumentConversionService
from storage_service import StorageService
from ai_document_generator_service import AIDocumentGeneratorService

# Initialize components
tender_repository = TenderRepository()
document_retrieval_service = DocumentRetrievalService()
document_conversion_service = DocumentConversionService(api_key="your_marker_api_key")
storage_service = StorageService()
ai_document_generator_service = AIDocumentGeneratorService(api_key="your_gemini_api_key")

# Initialize the workflow
workflow = AIDocumentsProcessingWorkflow(
    tender_repository=tender_repository,
    document_retrieval_service=document_retrieval_service,
    document_conversion_service=document_conversion_service,
    storage_service=storage_service,
    ai_document_generator_service=ai_document_generator_service
)

# Process a tender
result = await workflow.process_tender(
    tender_id="123",
    client_id="456",
    regenerate=True
)

print(f"AI document path: {result['ai_doc_path']}")
print(f"Chunks path: {result['chunks_path']}")
```

### 3. Working with Chunk References

To process a document with chunk references:

```python
from chunk_reference_utility import ChunkReferenceUtility

# Initialize the utility
reference_utility = ChunkReferenceUtility()

# Process a document with references
processed_text = reference_utility.process_document_with_references(
    document_path="path/to/ai_document.md",
    chunks_path="path/to/chunks.json",
    output_path="path/to/processed_document.md"
)

# Generate reference metadata for UI use
reference_metadata = reference_utility.generate_reference_metadata(
    document_path="path/to/ai_document.md",
    chunks_path="path/to/chunks.json",
    output_path="path/to/reference_metadata.json"
)
```

## Chunk Structure

Each chunk includes the following metadata:

- `chunk_id`: Unique identifier for the chunk
- `level`: Hierarchical level (0 = document, 1 = section, 2 = subsection, etc.)
- `title`: Title of the chunk (from the header)
- `parent_id`: ID of the parent chunk
- `pdf_path`: Path to the original PDF
- `page_number`: Page number in the original PDF
- `start_line`: Start line in the markdown
- `end_line`: End line in the markdown

## Reference Format

When referencing chunks in AI-generated content, use the format:

```
[chunk_id: chunk_0_1_caracteristicas_del_contrato]
```

These references can be converted to clickable links that redirect to the specific page in the original PDF.

## Frontend Integration

To integrate with a frontend:

1. Store the chunks and reference metadata
2. Replace chunk references with interactive elements
3. On click, redirect to the original PDF at the appropriate page

Example HTML for a chunk reference:

```html
<a href="path/to/original.pdf#page=5" class="chunk-reference" data-chunk-id="chunk_id">📄</a>
```

## Example Output Files

1. **Chunk JSON**: Hierarchical structure of chunks with metadata
2. **Combined Chunks JSON**: Flat list of all chunks for easier reference
3. **Processed Document**: AI-generated document with references replaced by links
4. **Reference Metadata**: JSON file with metadata about all references in a document

## Development

To contribute to this project:

1. Make changes to the code
2. Test with the test script
3. Update documentation as needed

Feel free to extend the functionality or improve the chunking algorithms.
