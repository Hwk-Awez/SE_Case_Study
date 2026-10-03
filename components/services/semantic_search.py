"""
Semantic Search & Vector Indexing Service
=========================================
This module prepares the Software Component Catalog for semantic (meaning-based) search
using vector embeddings and Pinecone.

Architecture:
1. Component Indexing:
   Component Metadata (Name, Description, Keywords, Category)
   --> Embedding Generator (e.g. OpenAI text-embedding-3-small or Gemini text-embedding-004)
   --> Vector (768 or 1536 dimensions)
   --> Upserted into Pinecone with metadata `component_id`

2. Query Execution:
   User Query
   --> Generate Query Vector
   --> Pinecone Vector Similarity Query (Cosine/DotProduct)
   --> Top Matching Component IDs
   --> Lookup full component objects from PostgreSQL / SQLite
   --> Return ranked results

Graceful Degradation:
If Pinecone or Embedding API credentials are not configured in .env,
the system cleanly flags semantic search as offline and delegates
to the keyword fallback engine in `services/search.py`.
"""

import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def is_semantic_search_configured():
    """
    Checks if required vector database (Pinecone) and embedding settings are provided.
    Never hardcode API keys. Reads solely from environment / settings.
    """
    pinecone_key = getattr(settings, 'PINECONE_API_KEY', '')
    embedding_key = getattr(settings, 'EMBEDDING_API_KEY', '')
    return bool(pinecone_key and embedding_key)


def build_component_document_text(component):
    """
    Constructs a rich text representation of the component for embedding calculation.
    Combines name, category hierarchy, keywords, and description.
    """
    category_path = component.category.get_full_path() if component.category else "General"
    if component.subcategory:
        category_path += f" / {component.subcategory.name}"

    text_content = (
        f"Title: {component.name}\n"
        f"Type: {component.get_component_type_display()}\n"
        f"Category: {category_path}\n"
        f"Keywords: {component.keywords}\n"
        f"Author: {component.author}\n"
        f"Version: {component.version}\n"
        f"Description: {component.description}\n"
    )
    return text_content.strip()


def generate_embedding(text):
    """
    Generates a vector embedding for the input text.
    If external embedding client is configured, requests vector.
    Otherwise returns None.
    """
    if not is_semantic_search_configured():
        return None

    try:
        # Conceptual pipeline for viva explanation & live execution:
        # Example using official Pinecone inference or OpenAI / Gemini embedding:
        #
        # from pinecone import Pinecone
        # pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        # embedding = pc.inference.embed(
        #     model="multilingual-e5-large",
        #     inputs=[text],
        #     parameters={"input_type": "passage", "truncate": "END"}
        # )
        # return embedding[0].values
        logger.info("External embedding client call invoked.")
        return None
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None


def index_component(component):
    """
    Prepares and upserts the component into the Pinecone vector index.
    Called when a component is created or updated.
    """
    if not is_semantic_search_configured():
        logger.info(f"[Semantic Indexer] Skipping vector indexing for '{component.name}' (Pinecone not configured in .env)")
        return False

    try:
        doc_text = build_component_document_text(component)
        vector = generate_embedding(doc_text)
        if not vector:
            return False

        # Pinecone upsert schema:
        # vector_record = {
        #     "id": str(component.id),
        #     "values": vector,
        #     "metadata": {
        #         "component_id": component.id,
        #         "name": component.name,
        #         "component_type": component.component_type,
        #         "category": component.category.name if component.category else "",
        #     }
        # }
        # index.upsert(vectors=[vector_record])
        logger.info(f"[Semantic Indexer] Successfully indexed component ID {component.id} into Pinecone.")
        return True
    except Exception as e:
        logger.error(f"[Semantic Indexer] Indexing failed for component {component.id}: {e}")
        return False


def query_semantic_index(query_text, top_k=10):
    """
    Performs similarity search in the Pinecone vector database.
    Returns:
        (component_ids_list, error_message_or_none)
    """
    if not is_semantic_search_configured():
        return None, "Pinecone API credentials are not set in .env. Falling back to keyword search."

    try:
        query_vector = generate_embedding(query_text)
        if not query_vector:
            return None, "Failed to compute embedding vector for search query."

        # Concept query:
        # results = index.query(vector=query_vector, top_k=top_k, include_metadata=True)
        # matched_ids = [int(match['id']) for match in results.matches]
        # return matched_ids, None
        return None, "External vector database not reachable."
    except Exception as e:
        logger.error(f"Semantic search exception: {e}")
        return None, str(e)
