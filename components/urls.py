from django.urls import path
from . import views

urlpatterns = [
    # Dashboard / Home
    path('', views.home_view, name='home'),

    # Component Repository
    path('components/', views.component_list_view, name='component_list'),
    path('components/add/', views.component_create_view, name='component_create'),
    path('components/<int:pk>/', views.component_detail_view, name='component_detail'),
    path('components/<int:pk>/edit/', views.component_update_view, name='component_update'),
    path('components/<int:pk>/delete/', views.component_delete_view, name='component_delete'),
    path('components/<int:pk>/download/', views.download_component_view, name='component_download'),
    path('components/<int:pk>/mark-reused/', views.mark_reused_view, name='component_mark_reused'),

    # Browse & Search
    path('browse/', views.browse_view, name='browse'),
    path('search/', views.search_view, name='search'),

    # Analytics & Reports
    path('analytics/', views.analytics_view, name='analytics'),
    path('reports/', views.reports_view, name='reports'),
    path('reports/export-csv/', views.export_report_csv_view, name='export_report_csv'),

    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
