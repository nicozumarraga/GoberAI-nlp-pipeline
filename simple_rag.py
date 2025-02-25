from openai import OpenAI
import numpy as np
import json
from fastembed import TextEmbedding
from typing import List, Dict, Any
from config import test_config

class SimpleRAG:
    def __init__(
        self,
        embeddings_data: List[Dict[str, Any]],
        api_key: str = None,
        model_name: str = "llama3-70b-8192",
        embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    ):
        """
        Initialize a simple RAG system

        Args:
            embeddings_data: List of embeddings with metadata
            api_key: Groq API key (will try to load from env vars if not provided)
            model_name: Groq model to use
            embedding_model_name: FastEmbed model used for query embedding
        """
        self.embeddings_data = embeddings_data
        self.api_key = api_key or test_config.GROQ_API_KEY
        self.model_name = model_name
        self.embedding_model_name = embedding_model_name

        # Initialize embedding model
        print(f"Loading query embedding model: {embedding_model_name}")
        self.embedding_model = TextEmbedding(embedding_model_name)

        if not self.api_key:
            raise ValueError("Groq API key not found. Please set GROQ_API_KEY env variable")

        # Initialize Groq client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1"
        )

    def find_relevant_chunks(self, query: str, top_k: int = 3) -> List[Dict]:
        """Find the most relevant chunks for a query"""
        # Embed the query
        query_embedding = list(self.embedding_model.embed([query]))[0]

        # Calculate similarities
        similarities = []
        for idx, emb_data in enumerate(self.embeddings_data):

            # Check if 'content' exists
            if 'content' not in emb_data:
                print(f"DEBUG: 'content' missing in embedding {idx}")
                # Try to use a safe fallback
                content = "No content available"
            else:
                content = emb_data['content']
                if not content or len(content.strip()) < 10:
                    print(f"DEBUG: Empty or very short content in embedding {idx}")

            doc_embedding = np.array(emb_data['embedding'])
            query_vec = np.array(query_embedding)

            # Calculate cosine similarity
            similarity = np.dot(query_vec, doc_embedding) / (
                np.linalg.norm(query_vec) * np.linalg.norm(doc_embedding)
            )

            # Get heading safely
            heading = emb_data['metadata'].get('heading', '')
            if not heading:
                # Try other potential heading fields from LangChain
                for i in range(1, 7):
                    key = f"heading{i}"
                    if key in emb_data['metadata'] and emb_data['metadata'][key]:
                        heading = emb_data['metadata'][key]
                        break

            similarities.append({
                'index': idx,
                'similarity': float(similarity),
                'content': (heading + "\n\n" if heading else "") + content,
                'metadata': emb_data['metadata']
            })

        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        return similarities[:top_k]

    def generate_prompt(self, query: str, relevant_chunks: List[Dict]) -> str:
        """Generate a prompt with context for the LLM"""
        context_parts = []

        for i, chunk in enumerate(relevant_chunks):
            source = chunk['metadata'].get('source', 'unknown source')
            heading = chunk['metadata'].get('heading', '')
            print(f"Chunk content for RAG: {chunk['content']}")
            context_parts.append(
                f"Document {i+1} from {source}"
                + (f" - Section: {heading}" if heading else "")
                + f"\n{chunk['content']}\n"
            )

        context = "\n\n".join(context_parts)

        prompt = f"""Basado en el contexto siguiente, responde a la pregunta del usuario. Si el contexto proporcionado
contiene la información para responder, dilo así. Si no está claro, indica que no puedes encontrar la información.

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:
"""
        return prompt

    def query(self, user_query: str, top_k: int = 3, temperature: float = 0.2) -> Dict:
        """
        Process a user query through the RAG pipeline

        Args:
            user_query: The user's question
            top_k: Number of relevant chunks to retrieve
            temperature: Temperature for LLM response (0.0-1.0)

        Returns:
            Dictionary with query results and metadata
        """
        # Find relevant chunks
        relevant_chunks = self.find_relevant_chunks(user_query, top_k)

        # Generate prompt
        prompt = self.generate_prompt(user_query, relevant_chunks)

        # Call Groq API
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Eres un asistente inteligente de licitaciones públicas en España."},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
                max_tokens=1024,
                stream=False
            )

            answer = response.choices[0].message.content

        except Exception as e:
            print(f"Error calling Groq API: {e}")
            answer = "Lo siento, ha ocurrido un error al procesar tu consulta."

        # Return results with metadata
        return {
            'query': user_query,
            'answer': answer,
            'sources': [
                {
                    'source': chunk['metadata'].get('source', 'unknown'),
                    'heading': chunk['metadata'].get('heading', '') or get_highest_heading(chunk['metadata']),
                    'similarity': chunk['similarity'],
                } for chunk in relevant_chunks
            ],
            'prompt': prompt
        }

def get_highest_heading(metadata):
    """Get the highest level heading from metadata."""
    for level in range(1, 7):
        key = f"heading{level}"
        if key in metadata and metadata[key]:
            return metadata[key]
    return ""
