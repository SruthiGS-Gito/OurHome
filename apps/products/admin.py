"""
apps/products/admin.py — Admin interface for the Product model.

After running migrations, go to /admin/ and you'll see "Products" in the sidebar.
This file controls HOW products are displayed and managed in the admin panel.
"""

from django.contrib import admin
from .models import Product, ViewHistory, SavedMaterial


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin configuration for Product model.

    Think of this as a spreadsheet view of your products table with:
    - Custom columns to display
    - Filters on the right sidebar
    - Search across multiple fields
    - Grouped editing form
    """

    # Columns shown in the product LIST (the table view at /admin/products/product/)
    list_display = (
        'name', 'brand', 'category', 'price', 'unit',
        'coastal_humid', 'heavy_rainfall', 'hot_dry', 'is_active',
    )

    # Clickable columns — clicking navigates to the edit page for that product.
    list_display_links = ('name',)

    # Columns you can edit INLINE in the list view (without opening edit page).
    # Useful for quickly toggling is_active or climate flags on multiple products.
    list_editable = ('is_active', 'coastal_humid', 'heavy_rainfall', 'hot_dry')

    # Filter sidebar on the right side of the list view.
    list_filter = (
        'category',
        'is_active',
        'coastal_humid',
        'heavy_rainfall',
        'hot_dry',
        'cold_hilly',
        'cyclone_prone',
    )

    # Search box — searches across these fields when you type in the search bar.
    search_fields = ('name', 'brand', 'manufacturer', 'is_code')

    # Default sort order in admin list (newest first — useful when adding products).
    ordering = ('-created_at',)

    # These fields are auto-set by Django — admin should not edit them manually.
    readonly_fields = ('slug', 'created_at', 'updated_at', 'average_rating', 'total_reviews')

    # Prepopulated fields: auto-fills slug from name AS YOU TYPE (live preview).
    # This is an admin JS feature — it shows you what the slug will look like.
    # We still auto-generate in save(), but this gives visual feedback.
    prepopulated_fields = {'slug': ('name',)}

    # FIELDSETS: organizes the product edit form into logical sections.
    # Without fieldsets, all 30+ fields appear as one long scrollable form.
    # With fieldsets, they're grouped under collapsible headings.
    # Format: ('Section Title', {'fields': ('field1', 'field2'), 'classes': ('collapse',)})
    # 'collapse' makes the section collapsible (click to expand).
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'brand', 'manufacturer', 'category', 'subcategory', 'slug'),
        }),
        ('Description & Specs', {
            'fields': ('description', 'specifications', 'is_code'),
        }),
        ('Pricing', {
            'fields': ('price', 'mrp', 'unit'),
            'description': 'price = typical market rate. mrp = legal maximum (printed on packaging).',
        }),
        ('Climate Suitability', {
            'fields': (
                'hot_dry', 'coastal_humid', 'heavy_rainfall',
                'cold_hilly', 'cyclone_prone',
            ),
            'description': (
                'Check the climates this product is SUITABLE for. '
                'Leave unchecked = NOT suitable. These power the climate warning badges.'
            ),
        }),
        ('Regional Availability', {
            'fields': ('seismic_zone', 'states_available', 'regional_notes'),
            'classes': ('collapse',),  # Collapsed by default — click to expand
        }),
        ('Image', {
            'fields': ('primary_image',),
        }),
        ('Status & Metadata', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
        ('Review Aggregates (Auto-computed)', {
            'fields': ('average_rating', 'total_reviews', 'rating_breakdown'),
            'classes': ('collapse',),
            'description': 'These are automatically updated when reviews are added. Do not edit manually.',
        }),
    )


@admin.register(ViewHistory)
class ViewHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['user__email', 'product__name']
    ordering = ['-viewed_at']
    readonly_fields = ['viewed_at']


@admin.register(SavedMaterial)
class SavedMaterialAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'saved_at']
    list_filter = ['saved_at']
    search_fields = ['user__email', 'product__name']
    ordering = ['-saved_at']
    readonly_fields = ['saved_at']
