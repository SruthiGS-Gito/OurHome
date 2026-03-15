"""
apps/reviews/models.py — Review model for OurHome's materials catalog.

Each Review is:
  - Written about one Product by one reviewer
  - Given a 1–5 star rating
  - Tagged with reviewer type (homeowner / contractor / architect / engineer)
  - Tagged with their climate zone (hot_dry / coastal_humid / etc.)
  - Moderated: only is_approved=True reviews appear on the site

WHY pre-approve reviews?
  - Prevents spam, fake ratings, and competitor attacks
  - Admin sets is_approved=True in the admin panel
  - Signal in signals.py recalculates product.average_rating etc. on each approve/delete

AGGREGATE FIELDS ON PRODUCT (updated by signals.py):
  product.average_rating  — average of all approved ratings
  product.total_reviews   — count of approved reviews
  product.rating_breakdown — {"5": 3, "4": 1, "3": 0, "2": 1, "1": 0}
"""

from django.conf import settings
from django.db import models


class Review(models.Model):

    RATING_CHOICES = [(i, str(i) + ' star' + ('' if i == 1 else 's')) for i in range(1, 6)]

    REVIEWER_TYPE_CHOICES = [
        ('homeowner',   'Homeowner'),
        ('contractor',  'Contractor'),
        ('architect',   'Architect'),
        ('designer',    'Interior Designer'),
        ('engineer',    'Civil Engineer'),
    ]

    CLIMATE_CHOICES = [
        ('hot_dry',        'Hot & Dry'),
        ('coastal_humid',  'Coastal & Humid'),
        ('heavy_rainfall', 'Heavy Rainfall'),
        ('cold_hilly',     'Cold & Hilly'),
        ('cyclone_prone',  'Cyclone-Prone Coast'),
    ]

    # ─────────────────────────────────────────────
    # CORE RELATIONS
    # ─────────────────────────────────────────────

    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='reviews',
        db_index=True,
    )

    # User FK is nullable: seeded / anonymous reviews don't require a login.
    # SET_NULL means if the user deletes their account, the review stays.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviews',
    )

    # ─────────────────────────────────────────────
    # REVIEW CONTENT
    # ─────────────────────────────────────────────

    rating = models.PositiveSmallIntegerField(
        choices=RATING_CHOICES,
        help_text="1 (terrible) to 5 (excellent)",
    )

    title = models.CharField(
        max_length=120,
        help_text="Short summary. Example: 'Perfect for coastal Kerala construction'",
    )

    review_text = models.TextField(
        help_text="Minimum 100 characters. Describe your actual experience.",
    )

    # ─────────────────────────────────────────────
    # REVIEWER IDENTITY
    # ─────────────────────────────────────────────
    # Stored separately from User so seeded / future anonymous reviews work.

    reviewer_name = models.CharField(
        max_length=100,
        help_text="Display name shown on the review card.",
    )

    reviewer_city = models.CharField(max_length=100, blank=True)
    reviewer_state = models.CharField(max_length=100, blank=True)

    reviewer_type = models.CharField(
        max_length=20,
        choices=REVIEWER_TYPE_CHOICES,
        default='homeowner',
    )

    # ─────────────────────────────────────────────
    # CONTEXT
    # ─────────────────────────────────────────────

    climate_type = models.CharField(
        max_length=20,
        choices=CLIMATE_CHOICES,
        blank=True,
        help_text="Reviewer's climate zone. Powers the 'Used in: Coastal Kerala' badge.",
    )

    use_case = models.CharField(
        max_length=200,
        blank=True,
        help_text="What was this used for? Example: 'Foundation of 2-storey house in Kochi'",
    )

    # ─────────────────────────────────────────────
    # ENGAGEMENT & MODERATION
    # ─────────────────────────────────────────────

    helpful_count = models.PositiveIntegerField(
        default=0,
        help_text="'Was this review helpful?' upvotes. Higher = shown first.",
    )

    is_approved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Only approved reviews appear on the product page.",
    )

    # ─────────────────────────────────────────────
    # TIMESTAMPS
    # ─────────────────────────────────────────────

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ─────────────────────────────────────────────
    # META
    # ─────────────────────────────────────────────

    class Meta:
        db_table = 'reviews'
        # Most helpful reviews first, newest as tiebreaker
        ordering = ['-helpful_count', '-created_at']
        indexes = [
            models.Index(fields=['product', 'is_approved'], name='review_product_approved_idx'),
        ]

    def __str__(self):
        return f"{self.reviewer_name} — {self.product.name} ({self.rating}★)"

    # ─────────────────────────────────────────────
    # PROPERTIES
    # ─────────────────────────────────────────────

    @property
    def reviewer_badge(self):
        """Returns (css_class, display_label) for the reviewer type chip."""
        return {
            'homeowner':  ('badge-homeowner',  'Homeowner'),
            'contractor': ('badge-contractor', 'Verified Contractor'),
            'architect':  ('badge-architect',  'Architect'),
            'designer':   ('badge-designer',   'Interior Designer'),
            'engineer':   ('badge-engineer',   'Civil Engineer'),
        }.get(self.reviewer_type, ('badge-homeowner', 'Homeowner'))

    @property
    def climate_label(self):
        """Human-readable label for the reviewer's climate zone."""
        return dict(self.CLIMATE_CHOICES).get(self.climate_type, '')

    @property
    def star_range(self):
        """Returns (filled_count, empty_count) for template star rendering."""
        return self.rating, (5 - self.rating)

    @property
    def location_display(self):
        parts = [p for p in [self.reviewer_city, self.reviewer_state] if p]
        return ', '.join(parts) if parts else ''
