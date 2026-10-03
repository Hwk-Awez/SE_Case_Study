from django import forms
from .models import Component, Category, ReuseRecord


class ComponentForm(forms.ModelForm):
    """
    Standard form for adding and editing reusable software components.
    Provides validation and clean HTML input classes.
    """
    class Meta:
        model = Component
        fields = [
            'name',
            'description',
            'component_type',
            'category',
            'subcategory',
            'keywords',
            'author',
            'version',
            'file',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. JWT Authentication Module'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 4,
                'placeholder': 'Explain what this component does, its inputs, outputs, and how developers can integrate it...'
            }),
            'component_type': forms.Select(attrs={'class': 'form-select'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'subcategory': forms.Select(attrs={'class': 'form-select'}),
            'keywords': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. jwt, auth, security, tokens (comma-separated)'
            }),
            'author': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Author name or team'
            }),
            'version': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '1.0.0'
            }),
            'file': forms.FileInput(attrs={'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Limit category to root categories or all categories
        self.fields['category'].queryset = Category.objects.filter(parent__isnull=True)
        self.fields['category'].empty_label = "-- Select Primary Category --"

        # Subcategories can be any non-root category
        self.fields['subcategory'].queryset = Category.objects.filter(parent__isnull=False)
        self.fields['subcategory'].empty_label = "-- Select Subcategory (Optional) --"
        self.fields['subcategory'].required = False


class ReuseRecordForm(forms.ModelForm):
    """
    Form for recording an instance of component reuse.
    """
    class Meta:
        model = ReuseRecord
        fields = ['reused_by', 'project_name', 'action', 'notes']
        widgets = {
            'reused_by': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Your Name or Team (e.g. Student Portal Team)'
            }),
            'project_name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Target Project (e.g. Hospital Management System)'
            }),
            'action': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g. Integrated into project / Forked and adapted'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Brief description of how the component was utilized or adapted...'
            }),
        }
