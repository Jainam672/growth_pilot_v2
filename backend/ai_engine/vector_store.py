"""
Vector Store — ChromaDB client for document storage and similarity search.
"""
import os
import logging
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

CHROMA_DB_PATH  = os.getenv("CHROMA_DB_PATH", "./vector_store/chroma_db")
COLLECTION_NAME = "business_knowledge"

_client     = None
_collection = None


def get_chroma_client():
    global _client
    if _client is None:
        os.makedirs(CHROMA_DB_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        logger.info(f"ChromaDB initialized at: {CHROMA_DB_PATH}")
    return _client


def get_collection():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
    return _collection


def add_documents(doc_ids: list, texts: list, embeddings: list, metadatas: list = None):
    """Add documents to ChromaDB collection in batches."""
    col = get_collection()
    if metadatas is None:
        metadatas = [{} for _ in texts]
    
    batch_size = 5000  # Safe batch size below ChromaDB's limit
    total_added = 0
    
    for i in range(0, len(texts), batch_size):
        end_idx = min(i + batch_size, len(texts))
        batch_ids = doc_ids[i:end_idx]
        batch_texts = texts[i:end_idx]
        batch_embeddings = embeddings[i:end_idx]
        batch_metadatas = metadatas[i:end_idx]
        
        col.add(
            ids=batch_ids,
            documents=batch_texts,
            embeddings=batch_embeddings,
            metadatas=batch_metadatas,
        )
        total_added += len(batch_texts)
        logger.info(f"Added batch of {len(batch_texts)} documents to ChromaDB.")
    
    logger.info(f"Total added: {total_added} documents to ChromaDB.")


def query_similar(query_embedding: list, n_results: int = 5) -> list:
    """Query ChromaDB for top-k similar document chunks."""
    col = get_collection()
    results = col.query(
        query_embeddings=[query_embedding],
        n_results=n_results,
    )
    # Return just the document texts
    return results["documents"][0] if results["documents"] else []


def count_documents() -> int:
    """Return number of documents indexed."""
    return get_collection().count()
