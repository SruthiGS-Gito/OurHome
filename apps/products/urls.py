"""
apps/products/urls.py — URL patterns for the materials catalog.

These are included in config/urls.py via:
    path('', include('apps.products.urls'))

So the final URLs are:
    /materials/           → product_list_view
    /materials/<slug>/    → product_detail_view

The <slug:slug> converter ensures:
- Only valid slug characters are matched (letters, numbers, hyphens)
- Rejects URLs with spaces or special characters (returns 404 automatically)
- Example match: /materials/ultratech-opc-53-grade-cement/
- Example reject: /materials/ultratech opc cement/ (space → 404)
"""

from django.urls import path
from . import views

urlpatterns = [
    path('materials/', views.product_list_view, name='product_list'),
    path('materials/<slug:slug>/', views.product_detail_view, name='product_detail'),
    path('materials/save/<slug:slug>/', views.toggle_save, name='toggle_save'),
    path('saved/', views.saved_materials_view, name='saved_materials'),
    path('saved/export/csv/', views.export_saved_materials_csv, name='export_saved_csv'),
    path('saved/remove/<slug:slug>/', views.remove_saved, name='remove_saved'),
    path('materials/<slug:slug>/review/', views.submit_review, name='submit_review'),
    path('material-analyzer/', views.material_analyzer_view, name='material_analyzer'),
    path('material-analyzer/bill/', views.bill_upload_view, name='bill_upload'),
    path('material-analyzer/chat/', views.bill_chat_view, name='bill_chat'),
    path('material-analyzer/clear/', views.bill_clear_view, name='bill_clear'),
]
