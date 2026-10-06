import re
from collections import defaultdict
from django.db.models import Q, Count
from components.models import Component, ComponentWord, ComponentKeyword, Category

# Standard stop-words to ignore during token-based indexing/search
STOP_WORDS = {
    'i', 'me', 'my', 'we', 'our', 'you', 'your', 'need', 'want',
    'looking', 'for', 'a', 'an', 'the', 'is', 'are', 'was', 'were',
    'to', 'of', 'in', 'on', 'at', 'by', 'with', 'from', 'some',
    'any', 'help', 'something', 'and', 'or', 'that', 'this', 'it'
}


def tokenize(text: str) -> list[str]:
    """Return lower-case word tokens from *text* (punctuation stripped)."""
    if not text:
        return []
    # Replace punctuation characters with spaces to avoid concatenating words
    cleaned = re.sub(r'[^\w\s-]', ' ', text.lower())
    raw_words = cleaned.split()
    tokens = set()
    for w in raw_words:
        w_clean = w.strip('-')
        if len(w_clean) >= 2 and w_clean not in STOP_WORDS:
            tokens.add(w_clean)
            # If word contains hyphens, also index individual parts
            if '-' in w_clean:
                subparts = w_clean.split('-')
                for part in subparts:
                    if len(part) >= 2 and part not in STOP_WORDS:
                        tokens.add(part)
                # Also include unhyphenated form (e.g. e-commerce -> ecommerce)
                tokens.add(w_clean.replace('-', ''))
    return list(tokens)


def index_component_tokens(component):
    """
    Extracts tokens from component metadata and synchronizes ComponentWord
    and ComponentKeyword tables for fast querying.
    """
    if not component or not component.pk:
        return

    try:
        # 1. Sync ComponentKeyword tags
        if component.keywords:
            kw_list = [k.strip().lower() for k in component.keywords.split(',') if k.strip()]
            existing_kws = set(ComponentKeyword.objects.filter(component=component).values_list('keyword', flat=True))
            new_kws = [ComponentKeyword(component=component, keyword=kw) for kw in set(kw_list) - existing_kws]
            if new_kws:
                ComponentKeyword.objects.bulk_create(new_kws, ignore_conflicts=True)

        # 2. Extract and sync ComponentWord tokens
        text_sources = [
            component.name or '',
            component.description or '',
            component.keywords or '',
            component.author or '',
            component.category.name if component.category else '',
            component.subcategory.name if component.subcategory else '',
        ]
        full_text = ' '.join(text_sources)
        tokens = set(tokenize(full_text))

        existing_words = set(ComponentWord.objects.filter(component=component).values_list('word', flat=True))
        to_create = [ComponentWord(component=component, word=w) for w in (tokens - existing_words)]
        if to_create:
            ComponentWord.objects.bulk_create(to_create, ignore_conflicts=True)

        to_delete = existing_words - tokens
        if to_delete:
            ComponentWord.objects.filter(component=component, word__in=to_delete).delete()
    except Exception as e:
        # Fail safe - indexing error should not crash request handling
        pass


def execute_token_search(tokens: list[str], component_type=None, category_id=None):
    """Legacy helper: find components that have any of the supplied *tokens*."""
    if not tokens:
        return Component.objects.none()

    qs = Component.objects.select_related('category', 'subcategory')
    if component_type in ['CODE', 'DESIGN']:
        qs = qs.filter(component_type=component_type)
    if category_id:
        qs = qs.filter(Q(category_id=category_id) | Q(subcategory_id=category_id))

    matched = ComponentWord.objects.filter(word__in=tokens, component__in=qs)
    annotated = matched.values('component').annotate(relevance=Count('id')).order_by('-relevance')
    component_ids = [item['component'] for item in annotated]
    ordering = {cid: i for i, cid in enumerate(component_ids)}
    components = Component.objects.filter(id__in=component_ids).select_related('category', 'subcategory')
    components = sorted(components, key=lambda c: ordering.get(c.id, 0))
    return components


def search_components(query_text, component_type=None, category_id=None, record_query=True):
    """
    Robust hybrid search service:
    1. Direct field substring matching on Component (name, keywords, description, author, category).
    2. Token-level matching across fields and ComponentWord / ComponentKeyword indexes.
    3. Intelligent relevance scoring so the closest matching components rank at the top.
    """
    cleaned_query = query_text.strip() if query_text else ""

    qs = Component.objects.select_related('category', 'subcategory')
    if component_type in ['CODE', 'DESIGN']:
        qs = qs.filter(component_type=component_type)
    if category_id:
        qs = qs.filter(Q(category_id=category_id) | Q(subcategory_id=category_id))

    if not cleaned_query:
        # Empty query -> return all filtered components
        results = list(qs.order_by('-created_at'))
        mode = 'direct'
        note = 'Displaying all components.'
    else:
        tokens = tokenize(cleaned_query)
        query_lower = cleaned_query.lower()
        scores = defaultdict(int)
        matched_map = {}

        # -------------------------------------------------------------
        # 1. Full-phrase / Direct Field Matches
        # -------------------------------------------------------------
        # Name match (highest weight)
        for comp in qs.filter(name__icontains=cleaned_query):
            matched_map[comp.id] = comp
            c_name_lower = comp.name.lower()
            if c_name_lower == query_lower:
                scores[comp.id] += 120
            elif c_name_lower.startswith(query_lower):
                scores[comp.id] += 80
            else:
                scores[comp.id] += 60

        # Keywords match
        for comp in qs.filter(keywords__icontains=cleaned_query):
            matched_map[comp.id] = comp
            scores[comp.id] += 50

        # Description match
        for comp in qs.filter(description__icontains=cleaned_query):
            matched_map[comp.id] = comp
            scores[comp.id] += 25

        # Author match
        for comp in qs.filter(author__icontains=cleaned_query):
            matched_map[comp.id] = comp
            scores[comp.id] += 20

        # Category / Subcategory match
        for comp in qs.filter(Q(category__name__icontains=cleaned_query) | Q(subcategory__name__icontains=cleaned_query)):
            matched_map[comp.id] = comp
            scores[comp.id] += 20

        # -------------------------------------------------------------
        # 2. Token-level Field Matches
        # -------------------------------------------------------------
        for token in tokens:
            token_q = (
                Q(name__icontains=token) |
                Q(keywords__icontains=token) |
                Q(description__icontains=token) |
                Q(author__icontains=token)
            )
            for comp in qs.filter(token_q):
                matched_map[comp.id] = comp
                c_name = comp.name.lower()
                c_kw = (comp.keywords or '').lower()
                c_desc = (comp.description or '').lower()
                if token in c_name:
                    scores[comp.id] += 30
                if token in c_kw:
                    scores[comp.id] += 20
                if token in c_desc:
                    scores[comp.id] += 10

        # -------------------------------------------------------------
        # 3. ComponentWord and ComponentKeyword Database Hits
        # -------------------------------------------------------------
        if tokens:
            try:
                word_matches = (
                    ComponentWord.objects
                    .filter(word__in=tokens, component__in=qs)
                    .values('component')
                    .annotate(cnt=Count('id'))
                )
                for item in word_matches:
                    cid = item['component']
                    scores[cid] += item['cnt'] * 15
                    if cid not in matched_map:
                        c_obj = qs.filter(id=cid).first()
                        if c_obj:
                            matched_map[cid] = c_obj

                kw_matches = (
                    ComponentKeyword.objects
                    .filter(keyword__in=tokens, component__in=qs)
                    .values('component')
                    .annotate(cnt=Count('id'))
                )
                for item in kw_matches:
                    cid = item['component']
                    scores[cid] += item['cnt'] * 20
                    if cid not in matched_map:
                        c_obj = qs.filter(id=cid).first()
                        if c_obj:
                            matched_map[cid] = c_obj
            except Exception:
                pass

        # -------------------------------------------------------------
        # 4. Relevance Sorting
        # -------------------------------------------------------------
        results = sorted(
            matched_map.values(),
            key=lambda c: (
                scores[c.id],
                c.reuse_count,
                c.view_count,
                c.created_at
            ),
            reverse=True
        )

        mode = 'keyword'
        note = f"Found {len(results)} matching component{'s' if len(results) != 1 else ''} for '{cleaned_query}'."

    # Record search query analytics
    if record_query and cleaned_query:
        from components.models import SearchQuery
        try:
            SearchQuery.objects.create(
                query_text=cleaned_query,
                results_count=len(results),
                search_mode=mode,
            )
        except Exception:
            pass

    return {
        'results': results,
        'count': len(results),
        'search_mode': mode,
        'note': note,
    }
