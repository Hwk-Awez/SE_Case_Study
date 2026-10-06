"""
Semantic Search & Vector Indexing Service (updated)
================================================
Now uses Pinecone (API key + index name) and LangChain's SentenceTransformer
embeddings for local vector generation. No external embedding API key required.
"""

import logging
import os
from pathlib import Path

from django.conf import settings

# LangChain & Sentence‑Transformer for local embeddings
from langchain_community.embeddings import SentenceTransformerEmbeddings

# Pinecone client
import pinecone

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def is_semantic_search_configured() -> bool:
    """Return True if Pinecone credentials are present.
    The embedding model is local (no external API key needed).
    """
    pinecone_key = getattr(settings, "PINECONE_API_KEY", "")
    index_name = getattr(settings, "PINECONE_INDEX_NAME", "")
    return bool(pinecone_key and index_name)

# Initialise Pinecone once (lazy singleton pattern)
_pinecone_client = None
_index = None

def _init_pinecone():
    global _pinecone_client, index
    if _pinecone_client is None:
        pinecone_key = settings.PINECONE_API_KEY
        environment = getattr(settings, "PINECONE_ENVIRONMENT", "") or "us-west1-gcp"
        pinecone.init(api_key=pinecone_key, environment=environment)
        _pinecone_client = pinecone
        index_name = settings.PINECONE_INDEX_NAME
        if index_name not in _pinecone_client.list_indexes():
            # Create a new index with a reasonable dimensionality (384 for MiniLM)
            logger.info(f"[Semantic] Creating Pinecone index '{index_name}' (384‑dim)")
            _pinecone_client.create_index(name=index_name, dimension=384, metric="cosine")
        index = _pinecone_client.Index(index_name)
    return index

# ---------------------------------------------------------------------------
# Embedding generation (local)
# ---------------------------------------------------------------------------

def _get_embeddings_model():
    """Return a LangChain SentenceTransformerEmbeddings instance.
    Uses the lightweight 'all‑MiniLM‑L6‑v2' model (384‑dim).
    """
    # Cache the model on the function object to avoid re‑loading
    if not hasattr(_get_embeddings_model, "_model"):
        _get_embeddings_model._model = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    return _get_embeddings_model._model


def generate_embedding(text: str):
    """Generate a 384‑dim embedding for *text* using the local model.
    Returns a list of floats or ``None`` on failure.
    """
    if not is_semantic_search_configured():
        return None
    try:
        model = _get_embeddings_model()
        embedding = model.embed_query(text)
        return embedding
    except Exception as e:
        logger.error(f"[Semantic] Embedding generation failed: {e}")
        return None

# ---------------------------------------------------------------------------
# Indexing helpers
# ---------------------------------------------------------------------------

def build_component_document_text(component):
    """Create a plain‑text representation of a component for embedding.
    Mirrors the original logic but kept here for clarity.
    """
    category_path = component.category.get_full_path() if component.category else "General"
    if component.subcategory:
        category_path += f" / {component.subcategory.name}"
    return (
        f"Title: {component.name}\n"
        f"Type: {component.get_component_type_display()}\n"
        f"Category: {category_path}\n"
        f"Keywords: {component.keywords}\n"
        f"Author: {component.author}\n"
        f"Version: {component.version}\n"
        f"Description: {component.description}"
    ).strip()

def index_component(component) -> bool:
    """Upsert a component into Pinecone.
    Called from the ``post_save`` signal (or manually after creation).
    Returns ``True`` on success.
    """
    if not is_semantic_search_configured():
        logger.info(f"[Semantic] Pinecone not configured – skipping index for '{component.name}'.")
        return False
    try:
        idx = _init_pinecone()
        doc_text = build_component_document_text(component)
        vector = generate_embedding(doc_text)
        if not vector:
            return False
        record = {
            "id": str(component.id),
            "values": vector,
            "metadata": {
                "component_id": component.id,
                "name": component.name,
                "component_type": component.component_type,
                "category": component.category.name if component.category else "",
                "subcategory": component.subcategory.name if component.subcategory else "",
            },
        }
        idx.upsert(vectors=[record])
        logger.info(f"[Semantic] Indexed component ID {component.id} into Pinecone.")
        return True
    except Exception as e:
        logger.error(f"[Semantic] Indexing failed for component {component.id}: {e}")
        return False

# ---------------------------------------------------------------------------
# Query helper
# ---------------------------------------------------------------------------

def query_semantic_index(query_text: str, top_k: int = 10):
    """Search Pinecone for *query_text* and return a list of component IDs.
    If Pinecone is unavailable the function returns ``(None, error_message)``.
    """
    if not is_semantic_search_configured():
        return None, "Pinecone not configured – falling back to keyword search."
    try:
        idx = _init_pinecone()
        query_vec = generate_embedding(query_text)
        if not query_vec:
            return None, "Failed to generate embedding for the query."
        results = idx.query(vector=query_vec, top_k=top_k, include_metadata=True)
        ids = [int(match["id"]) for match in results.get("matches", [])]
        return ids, None
    except Exception as e:
        logger.error(f"[Semantic] Query exception: {e}")
        return None, str(e)

"""End of semantic_search.py"""
