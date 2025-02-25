from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document
import os
import json

def langchain_chunk_markdown(markdown_path, output_dir=None, chunk_size=512, chunk_overlap=50):
    """
    Perform hierarchical chunking on markdown content using LangChain

    Args:
        markdown_path: Path to markdown file
        output_dir: Optional directory to save chunks
        chunk_size: Maximum chunk size for recursive splitting
        chunk_overlap: Overlap between chunks

    Returns:
        List of chunk objects and optionally list of saved file paths
    """
    # Read markdown content
    with open(markdown_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()

    # Define headers to split on
    headers_to_split_on = [
        ("#", "heading1"),
        ("##", "heading2"),
        ("###", "heading3"),
        ("####", "heading4"),
        ("#####", "heading5"),
        ("######", "heading6"),
    ]

    # Split text based on headers
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    header_docs = markdown_splitter.split_text(markdown_content)

    # Further split by size if needed
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""]
    )

    # Split each header section if it's too large
    all_docs = []
    for doc in header_docs:
        if len(doc.page_content) > chunk_size:
            smaller_docs = text_splitter.split_documents([doc])
            all_docs.extend(smaller_docs)
        else:
            all_docs.append(doc)

    # Convert to our chunk format
    chunks = []
    for i, doc in enumerate(all_docs):
        chunk = {
            'content': doc.page_content,
            'metadata': {
                'source': os.path.basename(markdown_path),
                'original_path': markdown_path,
                'chunk_num': i + 1,
                **doc.metadata
            }
        }
        chunks.append(chunk)

    # If output_dir is specified, save chunks to files
    if output_dir:
        chunk_files = []
        base_filename = os.path.splitext(os.path.basename(markdown_path))[0]

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        for i, chunk in enumerate(chunks):
            # Create heading-based filename
            heading = chunk['metadata'].get('heading1',
                      chunk['metadata'].get('heading2',
                      chunk['metadata'].get('heading3',
                      chunk['metadata'].get('heading4',
                      chunk['metadata'].get('heading5',
                      chunk['metadata'].get('heading6', 'section'))))))

            safe_heading = ''.join(c if c.isalnum() or c in [' ', '_', '-'] else '_'
                                  for c in heading)[:30].strip().replace(' ', '_')

            filename = f"{base_filename}_{i+1:03d}_{safe_heading}.md"
            filepath = os.path.join(output_dir, filename)

            # Create chunk file with metadata and content
            with open(filepath, 'w', encoding='utf-8') as f:
                # Write metadata as YAML front matter
                f.write("---\n")
                for key, value in chunk['metadata'].items():
                    f.write(f"{key}: {value}\n")
                f.write("---\n\n")

                # Write content
                f.write(chunk['content'])

            chunk_files.append(filepath)
            # Add filepath to chunk metadata
            chunks[i]['filepath'] = filepath

        # Create an index file
        index_path = os.path.join(output_dir, f"{base_filename}_index.json")
        with open(index_path, 'w', encoding='utf-8') as f:
            index_data = {
                'source': markdown_path,
                'total_chunks': len(chunks),
                'chunks': [{
                    'filepath': os.path.basename(chunk.get('filepath', '')),
                    'heading': get_highest_heading(chunk['metadata']),
                    'chunk_num': chunk['metadata']['chunk_num'],
                    'size': len(chunk['content'])
                } for chunk in chunks]
            }
            json.dump(index_data, f, indent=2)

        print(f"Created {len(chunks)} chunks from {markdown_path}")
        print(f"Saved chunk index to {index_path}")

        return chunks, chunk_files

    return chunks

def get_highest_heading(metadata):
    """Get the highest level heading from metadata."""
    for level in range(1, 7):
        key = f"heading{level}"
        if key in metadata and metadata[key]:
            return metadata[key]
    return "No heading"
