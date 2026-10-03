from datetime import datetime
from django.conf import settings
from .models import Component
from .services.semantic_search import is_semantic_search_configured


def catalog_context(request):
    """
    Global template context variables for component catalog:
    - Quick totals
    - Semantic search status indicator
    - Current year
    """
    return {
        'semantic_search_enabled': is_semantic_search_configured(),
        'current_year': datetime.now().year,
    }
