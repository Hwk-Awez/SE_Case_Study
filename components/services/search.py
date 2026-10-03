"""
Search Service Layer
====================
Provides a unified search interface for the Software Component Catalog.

Handles:
1. Intent check for Semantic Search (Pinecone Vector similarity).
2. Graceful fallback to multi-field relational search with concept/synonym expansion.
3. Automatic query logging into SearchQuery table for analytics.
"""

import re
from django.db.models import Q, Case, When, Value, IntegerField
from components.models import Component, SearchQuery, Category
from .semantic_search import is_semantic_search_configured, query_semantic_index


# Domain synonym map for natural query understanding in fallback mode
# Helps bridge common colloquial student/developer search terms with stored components
CONCEPT_SYNONYMS = {
    'login': ['auth', 'authentication', 'jwt', 'security', 'token', 'credentials', 'session'],
    'signin': ['auth', 'authentication', 'jwt', 'security'],
    'secure': ['security', 'auth', 'jwt', 'crypto', 'hash', 'token'],
    'checker': ['validation', 'validate', 'validator', 'format', 'verify'],
    'check': ['validation', 'validate', 'validator', 'verify'],
    'email': ['validation', 'email', 'format', 'regex'],
    'database': ['db', 'sql', 'connection', 'postgres', 'pool', 'schema', 'sqlite'],
    'db': ['database', 'sql', 'connection', 'orm'],
    'diagram': ['uml', 'architecture', 'er', 'design', 'class', 'flow'],
    'erd': ['er', 'diagram', 'database', 'schema', 'e-commerce'],
    'find': ['search', 'searching', 'binary', 'lookup'],
    'sorting': ['sort', 'algorithm', 'merge', 'quick', 'order'],
    'structure': ['architecture', 'mvc', 'design', 'pattern'],
}

STOP_WORDS = {
    'i', 'me', 'my', 'we', 'our', 'you', 'your', 'need', 'want', 'looking',
    'for', 'a', 'an', 'the', 'is', 'are', 'was', 'were', 'to', 'of', 'in',
    'on', 'at', 'by', 'with', 'from', 'something', 'help', 'some', 'any'
}


def tokenize_query(query_text):
    """
    Cleans punctuation and splits query into individual semantic tokens,
    excluding common filler stop words.
    """
    cleaned = re.sub(r'[^\w\s-]', '', query_text.lower())
    words = cleaned.split()
    tokens = [w for w in words if w not in STOP_WORDS and len(w) > 1]
    return tokens if tokens else [query_text.lower().strip()]


def execute_keyword_fallback(query_text, component_type=None, category_id=None):
    """
    Performs intelligent multi-field database search.
    Expands common terms (e.g. 'secure user login' -> 'auth', 'jwt')
    and scores matches higher if they occur in name or keywords.
    """
    tokens = tokenize_query(query_text)
    
    # Expand tokens with domain synonyms
    expanded_terms = set(tokens)
    for token in tokens:
        if token in CONCEPT_SYNONYMS:
            expanded_terms.update(CONCEPT_SYNONYMS[token])

    # Base QuerySet
    qs = Component.objects.select_related('category', 'subcategory')

    if component_type and component_type in ['CODE', 'DESIGN']:
        qs = qs.filter(component_type=component_type)

    if category_id:
        qs = qs.filter(Q(category_id=category_id) | Q(subcategory_id=category_id))

    # Construct Q filters across tokens
    exact_q = (
        Q(name__icontains=query_text) |
        Q(description__icontains=query_text) |
        Q(keywords__icontains=query_text) |
        Q(category__name__icontains=query_text)
    )

    token_q = Q()
    for term in expanded_terms:
        term_q = (
            Q(name__icontains=term) |
            Q(description__icontains=term) |
            Q(keywords__icontains=term) |
            Q(category__name__icontains=term) |
            Q(subcategory__name__icontains=term) |
            Q(author__icontains=term)
        )
        token_q |= term_q

    combined_q = exact_q | token_q
    filtered_qs = qs.filter(combined_q)

    # Relevance scoring: exact name/keywords matches are ranked higher
    scored_qs = filtered_qs.annotate(
        relevance=Case(
            When(name__icontains=query_text, then=Value(5)),
            When(keywords__icontains=query_text, then=Value(4)),
            When(description__icontains=query_text, then=Value(2)),
            default=Value(1),
            output_field=IntegerField()
        )
    ).order_by('-relevance', '-reuse_count', '-view_count')

    return list(scored_qs)


def search_components(query_text, component_type=None, category_id=None, record_query=True):
    """
    Main entry point for repository search.
    
    1. Tries semantic vector search if Pinecone is configured.
    2. Gracefully falls back to concept-expanded keyword search if not configured.
    3. Logs the search query for analytics and zero-result monitoring.
    
    Returns:
        {
            'results': list of Component objects,
            'count': int,
            'search_mode': 'semantic' | 'keyword',
            'note': str (explaining the search mechanism)
        }
    """
    cleaned_query = query_text.strip() if query_text else ""
    if not cleaned_query:
        # If empty query, return all matching filters
        qs = Component.objects.select_related('category', 'subcategory')
        if component_type and component_type in ['CODE', 'DESIGN']:
            qs = qs.filter(component_type=component_type)
        if category_id:
            qs = qs.filter(Q(category_id=category_id) | Q(subcategory_id=category_id))
        return {
            'results': list(qs),
            'count': qs.count(),
            'search_mode': 'direct',
            'note': 'Displaying all available components.'
        }

    search_mode = 'keyword'
    note = "Search executed via Local Keyword & Concept Engine (Pinecone credentials not configured)."
    results = []

    # 1. Attempt Semantic Search if configured
    if is_semantic_search_configured():
        matched_ids, err = query_semantic_index(cleaned_query)
        if matched_ids:
            search_mode = 'semantic'
            note = "Search executed via Pinecone Vector Similarity Search."
            # Retrieve components in vector score order
            components_dict = {
                c.id: c for c in Component.objects.filter(id__in=matched_ids).select_related('category', 'subcategory')
            }
            results = [components_dict[cid] for cid in matched_ids if cid in components_dict]
            
            # Apply optional filters
            if component_type and component_type in ['CODE', 'DESIGN']:
                results = [c for c in results if c.component_type == component_type]
            if category_id:
                results = [c for c in results if c.category_id == int(category_id) or c.subcategory_id == int(category_id)]

    # 2. Fallback to Local Search if semantic search was not configured or produced no results
    if not results and search_mode == 'keyword':
        results = execute_keyword_fallback(cleaned_query, component_type=component_type, category_id=category_id)

    # 3. Log query into SearchQuery table for analytics
    if record_query and cleaned_query:
        try:
            SearchQuery.objects.create(
                query_text=cleaned_query,
                results_count=len(results),
                search_mode=search_mode
            )
        except Exception:
            pass

    return {
        'results': results,
        'count': len(results),
        'search_mode': search_mode,
        'note': note
    }
