"""
apps/reviews/admin.py — Admin panel configuration for the Review model.

KEY WORKFLOW:
  1. User submits a review (is_approved=False by default)
  2. Admin sees it in the "Pending Approval" filter
  3. Admin reads the review, checks it's genuine
  4. Admin ticks the is_approved checkbox in list_editable
  5. Signal fires → product.average_rating and total_reviews update automatically

For demo purposes: seed_reviews sets is_approved=True directly,
so signals fire during seeding and products show real aggregates.
"""

from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):

    list_display = [
        'reviewer_name', 'product', 'rating', 'reviewer_type',
        'climate_type', 'reviewer_state', 'helpful_count',
        'is_approved', 'created_at',
    ]

    list_filter = ['is_approved', 'rating', 'reviewer_type', 'climate_type', 'reviewer_state']
    list_editable = ['is_approved']

    search_fields = ['reviewer_name', 'product__name', 'title', 'review_text']
    readonly_fields = ['created_at', 'updated_at', 'helpful_count']
    ordering = ['-created_at']

    fieldsets = [
        ('Review Content', {
            'fields': ['product', 'user', 'rating', 'title', 'review_text'],
        }),
        ('Reviewer', {
            'fields': ['reviewer_name', 'reviewer_city', 'reviewer_state', 'reviewer_type'],
        }),
        ('Context', {
            'fields': ['climate_type', 'use_case'],
        }),
        ('Moderation', {
            'fields': ['is_approved', 'helpful_count'],
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at'],
            'classes': ['collapse'],
        }),
    ]
