import os
from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class Category(models.Model):
    """
    Hierarchical classification category for software components.
    Example: Backend -> Authentication -> JWT
    """
    TYPE_CHOICES = [
        ('ALL', 'All Components'),
        ('CODE', 'Code'),
        ('DESIGN', 'Design'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subcategories'
    )
    component_type = models.CharField(
        max_length=10,
        choices=TYPE_CHOICES,
        default='ALL',
        help_text="Target component classification"
    )

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_full_path(self):
        """Returns breadcrumb path: e.g. Backend → Authentication → JWT"""
        if self.parent:
            return f"{self.parent.get_full_path()} → {self.name}"
        return self.name

    def is_root(self):
        return self.parent is None

    def __str__(self):
        return self.get_full_path()


class Component(models.Model):
    """
    Core model representing a reusable software component (Code or Design).
    """
    TYPE_CHOICES = [
        ('CODE', 'Code'),
        ('DESIGN', 'Design'),
    ]

    name = models.CharField(max_length=200, help_text="e.g. JWT Authentication Module")
    description = models.TextField(help_text="Detailed description of what the component does and how to use it.")
    component_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='CODE')
    
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='components',
        help_text="Primary category"
    )
    subcategory = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subcategory_components',
        help_text="Specific subcategory"
    )

    keywords = models.CharField(
        max_length=255,
        help_text="Comma-separated keywords or tags, e.g. 'jwt, auth, token, security'"
    )
    author = models.CharField(max_length=100, default='Anonymous Developer')
    version = models.CharField(max_length=20, default='1.0.0')
    file = models.FileField(upload_to='components/%Y/%m/', blank=True, null=True)

    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    reuse_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} (v{self.version})"

    def get_keywords_list(self):
        """Returns clean list of keywords for rendering badges"""
        if not self.keywords:
            return []
        return [kw.strip() for kw in self.keywords.split(',') if kw.strip()]

    def file_extension(self):
        if self.file:
            _, ext = os.path.splitext(self.file.name)
            return ext.lstrip('.').upper()
        return "N/A"

    def file_name(self):
        if self.file:
            return os.path.basename(self.file.name)
        return ""


class ComponentKeyword(models.Model):
    """
    Individual keyword mapping for direct lookups and relational indexing.
    """
    component = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='keyword_tags')
    keyword = models.CharField(max_length=60, db_index=True)

    class Meta:
        unique_together = ('component', 'keyword')

    def __str__(self):
        return f"{self.component.name} - {self.keyword}"


class ReuseRecord(models.Model):
    """
    Detailed audit log of whenever a developer marks a component as reused.
    """
    component = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='reuse_records')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_constraint=False)
    reused_by = models.CharField(max_length=150, help_text="Developer or student name")
    project_name = models.CharField(max_length=200, help_text="Target project or module")
    action = models.CharField(max_length=100, default="Integrated into project")
    notes = models.TextField(blank=True, help_text="Brief notes on how it was integrated")
    reused_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-reused_at']

    def __str__(self):
        return f"{self.component.name} reused by {self.reused_by} on {self.reused_at.strftime('%Y-%m-%d')}"


class ComponentUsage(models.Model):
    """
    Tracks component engagement metrics (views, downloads, reuse clicks).
    """
    ACTION_CHOICES = [
        ('VIEW', 'View'),
        ('DOWNLOAD', 'Download'),
        ('REUSE', 'Reuse'),
    ]

    component = models.ForeignKey(Component, on_delete=models.CASCADE, related_name='usages')
    action_type = models.CharField(max_length=15, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, db_constraint=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.get_action_type_display()} on {self.component.name} at {self.timestamp}"


class SearchQuery(models.Model):
    """
    Logs user searches for query analysis, trend identification,
    and discovering zero-result searches.
    """
    query_text = models.CharField(max_length=255, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    results_count = models.PositiveIntegerField(default=0)
    search_mode = models.CharField(
        max_length=50,
        default='keyword',
        help_text="Search engine utilized ('keyword' fallback or 'semantic' vector)"
    )

    class Meta:
        verbose_name_plural = 'Search Queries'
        ordering = ['-timestamp']

    def is_zero_result(self):
        return self.results_count == 0

    def __str__(self):
        return f"'{self.query_text}' ({self.results_count} results) [{self.search_mode}]"
