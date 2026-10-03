from django.contrib import admin
from .models import Category, Component, ComponentKeyword, ReuseRecord, ComponentUsage, SearchQuery


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'component_type', 'slug')
    list_filter = ('component_type', 'parent')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


class ComponentKeywordInline(admin.TabularInline):
    model = ComponentKeyword
    extra = 1


class ReuseRecordInline(admin.TabularInline):
    model = ReuseRecord
    extra = 0
    readonly_fields = ('reused_at',)


@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ('name', 'component_type', 'category', 'subcategory', 'author', 'version', 'reuse_count', 'view_count', 'download_count', 'created_at')
    list_filter = ('component_type', 'category', 'created_at')
    search_fields = ('name', 'description', 'keywords', 'author')
    inlines = [ComponentKeywordInline, ReuseRecordInline]


@admin.register(ReuseRecord)
class ReuseRecordAdmin(admin.ModelAdmin):
    list_display = ('component', 'reused_by', 'project_name', 'action', 'reused_at')
    list_filter = ('reused_at', 'action')
    search_fields = ('reused_by', 'project_name', 'component__name')


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query_text', 'results_count', 'search_mode', 'timestamp')
    list_filter = ('search_mode', 'timestamp')
    search_fields = ('query_text',)


@admin.register(ComponentUsage)
class ComponentUsageAdmin(admin.ModelAdmin):
    list_display = ('component', 'action_type', 'user', 'ip_address', 'timestamp')
    list_filter = ('action_type', 'timestamp')
