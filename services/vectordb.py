"""
services/vectordb.py
ChromaDB Integration - Vector storage and semantic retrieval.

ChromaDB stores:
  - chunk_text: the raw code/text content
  - embedding: 768-dim vector from Gemini
  - metadata: file path, language, line numbers, etc.
"""

import os
import chromadb
from chromadb.config import Settings

COLLECTION_NAME = "codebase_chunks"


def get_client(persist_directory: str) -> chromadb.Client:
    """Create or connect to a persistent ChromaDB client."""
    return chromadb.PersistentClient(
        path=persist_directory,
        settings=Settings(anonymized_telemetry=False)
    )


def get_or_create_collection(client: chromadb.Client):
    """Get or create the main collection. Uses cosine similarity."""
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}   # cosine similarity for semantic search
    )


def add_chunks(collection, chunks: list[dict], embeddings: list[list[float]]):
    """
    Add chunks and their embeddings to ChromaDB.
    ChromaDB requires: ids, embeddings, documents, metadatas
    """
    ids = [chunk['chunk_id'] for chunk in chunks]
    documents = [chunk['chunk_text'] for chunk in chunks]
    metadatas = [
        {
            'filepath': chunk.get('filepath', ''),
            'relative_path': chunk.get('relative_path', ''),
            'filename': chunk.get('filename', ''),
            'language': chunk.get('language', ''),
            'start_line': chunk.get('start_line', 0),
            'end_line': chunk.get('end_line', 0),
            'chunk_index': chunk.get('chunk_index', 0),
        }
        for chunk in chunks
    ]

    # Add in batches to avoid memory issues
    BATCH = 100
    for i in range(0, len(ids), BATCH):
        collection.add(
            ids=ids[i:i+BATCH],
            embeddings=embeddings[i:i+BATCH],
            documents=documents[i:i+BATCH],
            metadatas=metadatas[i:i+BATCH]
        )
    print(f"[VectorDB] Added {len(ids)} chunks to ChromaDB")


def semantic_search(collection, query_embedding: list[float], top_k: int = 5) -> list[dict]:
    """
    Search for the most semantically similar chunks to a query.
    Returns ranked list of results with metadata and relevance scores.
    """
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=['documents', 'metadatas', 'distances']
    )

    formatted = []
    for i in range(len(results['ids'][0])):
        formatted.append({
            'chunk_id': results['ids'][0][i],
            'content': results['documents'][0][i],
            'metadata': results['metadatas'][0][i],
            'score': 1 - results['distances'][0][i]  # convert distance to similarity
        })

    return formatted


def get_collection_stats(collection) -> dict:
    """Return basic stats about the collection."""
    count = collection.count()
    return {
        'total_chunks': count,
        'collection_name': COLLECTION_NAME
    }


def clear_collection(client: chromadb.Client):
    """Delete and recreate the collection (full re-index)."""
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    return get_or_create_collection(client)
