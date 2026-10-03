import csv
import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, FileResponse, Http404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.db.models import Count, Sum, Q
from django.utils import timezone

from .models import Component, Category, ReuseRecord, SearchQuery, ComponentUsage, ComponentKeyword
from .forms import ComponentForm, ReuseRecordForm
from .services.search import search_components
from .services.semantic_search import index_component, is_semantic_search_configured


# ==============================================================================
# 1. Home / Dashboard
# ==============================================================================
def home_view(request):
    """
    Main landing page:
    - Purpose statement
    - Key metrics (Total, Code, Design, Total Reuses)
    - Prominent search box
    - Recently added components
    """
    total_components = Component.objects.count()
    code_components = Component.objects.filter(component_type='CODE').count()
    design_components = Component.objects.filter(component_type='DESIGN').count()
    
    # Calculate total reuses
    total_reuses = Component.objects.aggregate(total=Sum('reuse_count'))['total'] or 0

    # Recently added components (last 6)
    recent_components = Component.objects.select_related('category', 'subcategory')[:6]

    context = {
        'total_components': total_components,
        'code_components': code_components,
        'design_components': design_components,
        'total_reuses': total_reuses,
        'recent_components': recent_components,
    }
    return render(request, 'components/home.html', context)


# ==============================================================================
# 2. Component Repository (List & Filter)
# ==============================================================================
def component_list_view(request):
    """
    Displays the catalog of software components with type & category filtering,
    and sorting options.
    """
    comp_type = request.GET.get('type', '')
    category_slug = request.GET.get('category', '')
    sort_by = request.GET.get('sort', '-created_at')

    components_qs = Component.objects.select_related('category', 'subcategory')

    if comp_type in ['CODE', 'DESIGN']:
        components_qs = components_qs.filter(component_type=comp_type)

    selected_category = None
    if category_slug:
        selected_category = Category.objects.filter(slug=category_slug).first()
        if selected_category:
            components_qs = components_qs.filter(
                Q(category=selected_category) | Q(subcategory=selected_category)
            )

    # Valid sort fields
    valid_sorts = {
        'newest': '-created_at',
        'reused': '-reuse_count',
        'views': '-view_count',
        'downloads': '-download_count',
        'name': 'name',
    }
    order_field = valid_sorts.get(sort_by, '-created_at')
    components_qs = components_qs.order_by(order_field)

    categories = Category.objects.filter(parent__isnull=True)

    context = {
        'components': components_qs,
        'categories': categories,
        'selected_type': comp_type,
        'selected_category': selected_category,
        'selected_sort': sort_by,
        'count': components_qs.count(),
    }
    return render(request, 'components/component_list.html', context)


# ==============================================================================
# 3. Component Details & Actions
# ==============================================================================
def component_detail_view(request, pk):
    """
    Full component details page:
    - Increments view count on visit
    - Shows metadata and downloads
    - Lists reuse history
    - Provides modal for recording new reuse
    """
    component = get_object_or_404(Component.objects.select_related('category', 'subcategory'), pk=pk)

    # Increment view count
    Component.objects.filter(pk=pk).update(view_count=component.view_count + 1)
    component.refresh_from_db(fields=['view_count'])

    # Track usage event
    ComponentUsage.objects.create(
        component=component,
        action_type='VIEW',
        user=request.user if request.user.is_authenticated else None,
        ip_address=request.META.get('REMOTE_ADDR')
    )

    reuse_form = ReuseRecordForm()
    reuse_history = component.reuse_records.all()

    context = {
        'component': component,
        'reuse_form': reuse_form,
        'reuse_history': reuse_history,
    }
    return render(request, 'components/component_detail.html', context)


def download_component_view(request, pk):
    """
    Handles downloading the component's file.
    Increments download_count on the component.
    """
    component = get_object_or_404(Component, pk=pk)

    if not component.file:
        messages.error(request, "This component does not have an attached file.")
        return redirect('component_detail', pk=pk)

    # Increment download count
    Component.objects.filter(pk=pk).update(download_count=component.download_count + 1)

    # Record usage
    ComponentUsage.objects.create(
        component=component,
        action_type='DOWNLOAD',
        user=request.user if request.user.is_authenticated else None,
        ip_address=request.META.get('REMOTE_ADDR')
    )

    try:
        response = FileResponse(component.file.open('rb'), as_attachment=True, filename=component.file_name())
        return response
    except FileNotFoundError:
        raise Http404("File not found on storage.")


def mark_reused_view(request, pk):
    """
    Increments reuse count and creates a persistent ReuseRecord.
    """
    component = get_object_or_404(Component, pk=pk)

    if request.method == 'POST':
        form = ReuseRecordForm(request.POST)
        if form.is_valid():
            record = form.save(commit=False)
            record.component = component
            if request.user.is_authenticated:
                record.user = request.user
            record.save()

            # Increment reuse_count
            Component.objects.filter(pk=pk).update(reuse_count=component.reuse_count + 1)

            # Record usage
            ComponentUsage.objects.create(
                component=component,
                action_type='REUSE',
                user=request.user if request.user.is_authenticated else None,
                ip_address=request.META.get('REMOTE_ADDR')
            )

            messages.success(request, f"Marked '{component.name}' as reused! Thank you for contributing to reuse tracking.")
        else:
            messages.error(request, "Failed to record reuse. Please check the form fields.")

    return redirect('component_detail', pk=pk)


# ==============================================================================
# 4. Add & Edit Component
# ==============================================================================
def component_create_view(request):
    """
    Form to add a new reusable component with validation and file upload.
    """
    if request.method == 'POST':
        form = ComponentForm(request.POST, request.FILES)
        if form.is_valid():
            component = form.save()

            # Index keywords
            if component.keywords:
                for kw in component.get_keywords_list():
                    ComponentKeyword.objects.get_or_create(component=component, keyword=kw.lower())

            # Conceptually trigger vector indexing
            index_component(component)

            messages.success(request, f"Component '{component.name}' successfully added to the catalog!")
            return redirect('component_detail', pk=component.pk)
    else:
        form = ComponentForm()

    return render(request, 'components/component_form.html', {'form': form, 'title': 'Add Component'})


def component_update_view(request, pk):
    """
    Form to edit an existing component.
    """
    component = get_object_or_404(Component, pk=pk)

    if request.method == 'POST':
        form = ComponentForm(request.POST, request.FILES, instance=component)
        if form.is_valid():
            component = form.save()

            # Re-index keywords
            ComponentKeyword.objects.filter(component=component).delete()
            if component.keywords:
                for kw in component.get_keywords_list():
                    ComponentKeyword.objects.get_or_create(component=component, keyword=kw.lower())

            # Trigger vector re-indexing
            index_component(component)

            messages.success(request, f"Component '{component.name}' updated successfully.")
            return redirect('component_detail', pk=component.pk)
    else:
        form = ComponentForm(instance=component)

    return render(request, 'components/component_form.html', {'form': form, 'title': 'Edit Component', 'component': component})


# ==============================================================================
# 5. Delete Component
# ==============================================================================
def component_delete_view(request, pk):
    """
    Confirmation and deletion of a component.
    """
    component = get_object_or_404(Component, pk=pk)

    if request.method == 'POST':
        name = component.name
        component.delete()
        messages.success(request, f"Component '{name}' was deleted.")
        return redirect('component_list')

    return render(request, 'components/component_confirm_delete.html', {'component': component})


# ==============================================================================
# 6. Browse Components (Hierarchical View)
# ==============================================================================
def browse_view(request):
    """
    Enables users to explore components hierarchically by:
    Type -> Category -> Subcategory without relying on search.
    """
    selected_cat_id = request.GET.get('category')
    selected_subcat_id = request.GET.get('subcategory')
    selected_type = request.GET.get('type')

    root_categories = Category.objects.filter(parent__isnull=True).prefetch_related('subcategories')

    components = []
    active_selection_title = None

    if selected_subcat_id:
        subcat = Category.objects.filter(id=selected_subcat_id).first()
        if subcat:
            active_selection_title = f"{subcat.get_full_path()}"
            components = Component.objects.filter(subcategory=subcat).select_related('category', 'subcategory')
    elif selected_cat_id:
        cat = Category.objects.filter(id=selected_cat_id).first()
        if cat:
            active_selection_title = f"{cat.name}"
            components = Component.objects.filter(Q(category=cat) | Q(subcategory=cat)).select_related('category', 'subcategory')
    elif selected_type in ['CODE', 'DESIGN']:
        active_selection_title = f"All {selected_type.title()} Components"
        components = Component.objects.filter(component_type=selected_type).select_related('category', 'subcategory')

    context = {
        'root_categories': root_categories,
        'components': components,
        'active_selection_title': active_selection_title,
        'selected_cat_id': int(selected_cat_id) if selected_cat_id else None,
        'selected_subcat_id': int(selected_subcat_id) if selected_subcat_id else None,
        'selected_type': selected_type,
    }
    return render(request, 'components/browse.html', context)


# ==============================================================================
# 7. Search View
# ==============================================================================
def search_view(request):
    """
    Executes search with semantic check and fallback engine.
    Records search queries for analytics.
    """
    query = request.GET.get('q', '').strip()
    comp_type = request.GET.get('type', '')
    cat_id = request.GET.get('category', '')

    search_result = search_components(query, component_type=comp_type, category_id=cat_id)

    categories = Category.objects.filter(parent__isnull=True)

    context = {
        'query': query,
        'results': search_result['results'],
        'count': search_result['count'],
        'search_mode': search_result['search_mode'],
        'search_note': search_result['note'],
        'categories': categories,
        'selected_type': comp_type,
        'selected_cat_id': int(cat_id) if cat_id else None,
    }
    return render(request, 'components/search_results.html', context)


# ==============================================================================
# 8. Usage Statistics & Analytics
# ==============================================================================
def analytics_view(request):
    """
    Displays usage statistics, top components, query analytics, and zero-result queries.
    """
    # Top metrics
    most_viewed = Component.objects.order_by('-view_count')[:5]
    most_downloaded = Component.objects.order_by('-download_count')[:5]
    most_reused = Component.objects.order_by('-reuse_count')[:5]

    # Search Query Analytics
    total_searches = SearchQuery.objects.count()
    zero_result_searches = SearchQuery.objects.filter(results_count=0)
    zero_result_count = zero_result_searches.count()

    # Most frequent search terms
    frequent_queries = (
        SearchQuery.objects.values('query_text')
        .annotate(total_hits=Count('query_text'))
        .order_by('-total_hits')[:8]
    )

    # Recent zero result queries
    recent_zero_queries = zero_result_searches.order_by('-timestamp')[:8]

    # Recent general search queries
    recent_queries = SearchQuery.objects.order_by('-timestamp')[:10]

    context = {
        'most_viewed': most_viewed,
        'most_downloaded': most_downloaded,
        'most_reused': most_reused,
        'total_searches': total_searches,
        'zero_result_count': zero_result_count,
        'frequent_queries': frequent_queries,
        'recent_zero_queries': recent_zero_queries,
        'recent_queries': recent_queries,
    }
    return render(request, 'components/analytics.html', context)


# ==============================================================================
# 9. Reports & Exports
# ==============================================================================
def reports_view(request):
    """
    Summary repository report with statistics, top contributors,
    and options to print or export as CSV.
    """
    total_components = Component.objects.count()
    code_components = Component.objects.filter(component_type='CODE').count()
    design_components = Component.objects.filter(component_type='DESIGN').count()
    category_count = Category.objects.count()

    top_viewed = Component.objects.order_by('-view_count').first()
    top_downloaded = Component.objects.order_by('-download_count').first()
    top_reused = Component.objects.order_by('-reuse_count').first()

    total_searches = SearchQuery.objects.count()
    zero_result_searches = SearchQuery.objects.filter(results_count=0).count()
    total_reuses = Component.objects.aggregate(total=Sum('reuse_count'))['total'] or 0

    components = Component.objects.select_related('category', 'subcategory').order_by('-reuse_count', '-created_at')

    context = {
        'total_components': total_components,
        'code_components': code_components,
        'design_components': design_components,
        'category_count': category_count,
        'top_viewed': top_viewed,
        'top_downloaded': top_downloaded,
        'top_reused': top_reused,
        'total_searches': total_searches,
        'zero_result_searches': zero_result_searches,
        'total_reuses': total_reuses,
        'components': components,
        'generated_at': timezone.now(),
    }
    return render(request, 'components/reports.html', context)


def export_report_csv_view(request):
    """
    Exports a clean CSV file of all components and their reuse metrics.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="component_repository_report.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'ID',
        'Component Name',
        'Type',
        'Category',
        'Subcategory',
        'Author',
        'Version',
        'Views',
        'Downloads',
        'Reuses',
        'Date Added',
        'Keywords'
    ])

    for comp in Component.objects.select_related('category', 'subcategory').all():
        writer.writerow([
            comp.id,
            comp.name,
            comp.get_component_type_display(),
            comp.category.name if comp.category else '',
            comp.subcategory.name if comp.subcategory else '',
            comp.author,
            comp.version,
            comp.view_count,
            comp.download_count,
            comp.reuse_count,
            comp.created_at.strftime('%Y-%m-%d'),
            comp.keywords
        ])

    return response


# ==============================================================================
# 10. Authentication Views (Simple Login / Logout)
# ==============================================================================
def login_view(request):
    """Simple developer login - strictly login only, redirects to target or home upon success"""
    if request.user.is_authenticated:
        return redirect('home')

    next_url = request.GET.get('next') or request.POST.get('next') or ''

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Logged in successfully as {user.username}.")
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password. Please verify your credentials.")
    else:
        form = AuthenticationForm()

    return render(request, 'components/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    """Developer logout - logs out and returns to login gateway"""
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')
