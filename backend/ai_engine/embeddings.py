"""
Embeddings module — wraps SentenceTransformers for ChromaDB ingestion and querying.
"""
import os
import logging

logger = logging.getLogger(__name__)

_embed_model = None


def get_embedding_model():
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info("Loading embedding model: all-MiniLM-L6-v2")
        _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model


def embed_text(text: str) -> list:
    """Embed a single string and return a float list."""
    model = get_embedding_model()
    return model.encode(text).tolist()


def embed_batch(texts: list) -> list:
    """Embed a list of strings."""
    model = get_embedding_model()
    return model.encode(texts).tolist()
