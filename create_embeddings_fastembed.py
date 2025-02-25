from fastembed import TextEmbedding
import numpy as np
import json
import os
from pathlib import Path

def create_embeddings(chunks, output_dir=None, model_name="BAAI/bge-small-en-v1.5"):
    """
    Create embeddings for chunks using FastEmbed

    Args:
        chunks: List of chunk objects (each containing 'content' and 'metadata')
        output_dir: Optional directory to save embeddings (if None, won't save files)
        model_name: FastEmbed model to use

    Returns:
        List of embeddings with metadata and optionally index file path
    """
    # Initialize the embedding model
    print(f"Loading embedding model: {model_name}")
    embedding_model = TextEmbedding(model_name)

    # Process each chunk
    embeddings_data = []

    for chunk in chunks:
        text_content = chunk['content']
        metadata = chunk['metadata']

        # Generate embedding
        embeddings = list(embedding_model.embed([text_content]))
        if embeddings:
            embedding_vector = embeddings[0].tolist()

            # Create embedding record
            embedding_data = {
                'metadata': metadata,
                'embedding_dim': len(embedding_vector),
                'model': model_name,
                'embedding': embedding_vector,
                'content': text_content
            }

            # Add to results
            embeddings_data.append(embedding_data)

    # If output directory is specified, save embeddings
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        saved_embeddings = []

        for idx, emb_data in enumerate(embeddings_data):
            # Get source info
            source = emb_data['metadata'].get('source', 'unknown')
            chunk_num = emb_data['metadata'].get('chunk_num', idx)

            # Save individual embedding file
            file_base = f"{os.path.splitext(source)[0]}_{chunk_num}"
            embedding_file = os.path.join(output_dir, f"{file_base}.json")

            with open(embedding_file, 'w', encoding='utf-8') as f:
                json.dump(emb_data, f)

            # For the index, don't include the actual vectors
            saved_data = {
                'metadata': emb_data['metadata'],
                'embedding_dim': emb_data['embedding_dim'],
                'model': model_name,
                'embedding_file': os.path.basename(embedding_file)
            }
            saved_embeddings.append(saved_data)

        # Create embeddings index
        index_path = os.path.join(output_dir, "embeddings_index.json")
        with open(index_path, 'w', encoding='utf-8') as f:
            index_data = {
                'model': model_name,
                'embedding_count': len(saved_embeddings),
                'dimension': embeddings_data[0]['embedding_dim'] if embeddings_data else 0,
                'embeddings': saved_embeddings
            }
            json.dump(index_data, f, indent=2)

        print(f"Created {len(embeddings_data)} embeddings with model {model_name}")
        print(f"Saved embeddings index to {index_path}")

        return embeddings_data, index_path

    return embeddings_data
