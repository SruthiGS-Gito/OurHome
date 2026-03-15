"""
apps/products/models.py — The Product model for OurHome's material catalog.

This is the core of the platform. Every product (cement, steel, paint, etc.)
is a row in this table. The climate suitability fields are what makes OurHome
different from a generic product catalog.

HOW MODELS BECOME DATABASE TABLES:
- Django reads this file and generates SQL automatically.
- Each class = one table. Each attribute = one column.
- You never write SQL — Django handles it.
- When you add/change fields, you run:
    python manage.py makemigrations   ← generates the SQL
    python manage.py migrate          ← applies it to the database
"""

from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Product(models.Model):
    """
    Represents one construction material in the OurHome catalog.

    The model has 5 logical sections:
    1. Identity       — name, brand, category, what it is
    2. Technical      — specs, IS code, price, unit
    3. Climate        — which climates it's suitable for
    4. Regional       — where in India it's available
    5. Metadata       — slug, timestamps, active flag
    """

    # ─────────────────────────────────────────────
    # SECTION 1: CATEGORY CHOICES
    # ─────────────────────────────────────────────
    # These are the construction phases a material belongs to.
    # choices= creates a dropdown in forms and admin instead of a free-text field.
    # The format is: (database_value, human_readable_label)
    # Database stores 'cement'. Admin/forms show 'Cement'.
    CATEGORY_CHOICES = [
        # Original 8 categories
        ('cement',        'Cement'),
        ('steel',         'Steel & TMT Bars'),
        ('brick',         'Bricks & Blocks'),
        ('sand',          'Sand'),
        ('aggregate',     'Aggregate'),
        ('tile',          'Tiles & Flooring'),
        ('paint',         'Paint & Coatings'),
        ('waterproofing', 'Waterproofing'),
        # Phase 2 expansion categories
        ('concrete',      'Concrete'),
        ('hardware',      'Fasteners & Hardware'),
        ('wood',          'Wood & Timber'),
        ('roofing',       'Roofing'),
        ('windows',       'Windows & Doors'),
        ('plumbing',      'Plumbing'),
        ('electrical',    'Electrical'),
        ('plaster',       'Plaster & Finishes'),
        ('fixtures',      'Fixtures & Fittings'),
    ]

    PHASE_CHOICES = [
        ('foundation', 'Foundation & Substructure'),
        ('framing',    'Framing & Structure'),
        ('exterior',   'Exterior & Roofing'),
        ('roughin',    'Rough-In (Plumbing & Electrical)'),
        ('finishing',  'Interior Finishing'),
    ]

    SEISMIC_ZONE_CHOICES = [
        ('Zone II',  'Zone II (Low Damage Risk)'),
        ('Zone III', 'Zone III (Moderate Damage Risk)'),
        ('Zone IV',  'Zone IV (High Damage Risk)'),
        ('Zone V',   'Zone V (Very High Damage Risk)'),
    ]

    # ─────────────────────────────────────────────
    # SECTION 2: IDENTITY FIELDS
    # ─────────────────────────────────────────────

    name = models.CharField(
        max_length=200,
        help_text="Full product name. Example: 'UltraTech OPC 53 Grade Cement'",
    )

    brand = models.CharField(
        max_length=100,
        help_text="Brand name. Example: 'UltraTech', 'JSW Steel', 'Asian Paints'",
    )

    manufacturer = models.CharField(
        max_length=200,
        blank=True,
        help_text="Company that manufactures the product. Often same as brand.",
    )

    # choices= restricts input to our predefined list.
    # This prevents typos like 'Cement' or 'cemnt'.
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        db_index=True,  # db_index=True makes filtering by category FAST.
                        # Without index: database scans every row (slow for 10,000 products).
                        # With index: database jumps directly to matching rows (instant).
    )

    subcategory = models.CharField(
        max_length=100,
        blank=True,     # blank=True means form field is optional.
        help_text="Optional. Example: 'OPC 53 Grade', 'TMT Fe500D', 'Premium Emulsion'",
    )

    description = models.TextField(
        help_text="Detailed product description. What it is, what it does, key benefits.",
    )

    # ─────────────────────────────────────────────
    # SECTION 3: TECHNICAL FIELDS
    # ─────────────────────────────────────────────

    # JSONField stores a Python dictionary as JSON in the database.
    # Perfect for technical specifications that vary by product type:
    #   Cement: {"strength_mpa": "53", "setting_time_min": "30", "fineness": "300 m²/kg"}
    #   Steel:  {"grade": "Fe500D", "yield_strength": "500 N/mm²", "diameter_mm": "10"}
    #   Paint:  {"coverage_sqft_per_liter": "90", "drying_time_hr": "2", "finish": "Matte"}
    # Using JSONField instead of individual columns because:
    #   - Cement has completely different specs than steel
    #   - We'd need 30+ columns to cover all product types (wasteful)
    #   - JSONField lets each product store only its relevant specs
    specifications = models.JSONField(
        default=dict,   # default=dict creates an empty {} when not provided.
                        # Never use default={} directly — Python reuses the same dict
                        # across all instances (a famous Python gotcha).
                        # default=dict creates a fresh {} for each product.
        blank=True,
        help_text="Technical specs as key-value pairs. Example: {\"strength\": \"53 MPa\"}",
    )

    # price = what shops typically charge in the market (varies by city/shop).
    # mrp = Maximum Retail Price printed on packaging (legal ceiling — no shop can charge more).
    # WHY both? The Quote Verifier needs to catch if a contractor quotes ABOVE mrp.
    # "Contractor quoted ₹420/bag. MRP is ₹400/bag. That's ILLEGAL." ← this comparison is only
    # possible if we store both values separately.
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Typical market price. Example: 385.00 (₹385 per bag)",
    )

    mrp = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Maximum Retail Price (printed on packaging). No shop can charge above this.",
    )

    # DecimalField vs FloatField for money:
    # FloatField uses binary floating point → 0.1 + 0.2 = 0.30000000000000004 (rounding error!)
    # DecimalField uses exact decimal arithmetic → 0.1 + 0.2 = 0.3 (exact)
    # Always use DecimalField for money.

    unit = models.CharField(
        max_length=50,
        help_text="Unit of measurement. Examples: 'bag', 'kg', 'piece', 'litre', 'sqft', 'meter'",
    )

    is_code = models.CharField(
        max_length=100,
        blank=True,
        help_text="Indian Standard code. Example: 'IS 269:2015' for OPC cement.",
    )

    phase = models.CharField(
        max_length=20,
        choices=PHASE_CHOICES,
        blank=True,
        db_index=True,
        help_text="Construction phase this material is primarily used in.",
    )

    # ─────────────────────────────────────────────
    # SECTION 4: CLIMATE SUITABILITY FIELDS
    # ─────────────────────────────────────────────
    # These are the KILLER FEATURE.
    #
    # Each field is a BooleanField (True/False) — "is this product suitable for X climate?"
    #
    # WHY Boolean instead of a list or text?
    #
    # Option A — TEXT (Bad):
    #   suitable_climates = "coastal, rainfall"
    #   Problem: Can't filter. Product.objects.filter(suitable_climates='coastal') doesn't
    #   work reliably because 'coastal' might be 'coastal_humid' in another product.
    #
    # Option B — JSONField list (Medium):
    #   suitable_climates = ["coastal_humid", "heavy_rainfall"]
    #   Problem: Django can filter JSONField but it's slow and complex:
    #   Product.objects.filter(suitable_climates__contains='coastal_humid')
    #   This works but scans JSON text — much slower than indexed boolean.
    #
    # Option C — BooleanFields (Best) ← WE USE THIS:
    #   coastal_humid = True, heavy_rainfall = True
    #   Query: Product.objects.filter(coastal_humid=True) — uses database index, instant.
    #   Add db_index=True and filtering 10,000 products takes <1ms.
    #
    # Real-world user query: "Show me materials suitable for coastal Kerala"
    #   → Product.objects.filter(coastal_humid=True, is_active=True)
    #   → Database uses index, returns matching rows instantly.
    #
    # default=False means: unless explicitly marked suitable, assume NOT suitable.
    # This is safer than defaulting to True (better to miss a recommendation than
    # recommend a damaging material).

    hot_dry = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Suitable for Hot & Dry Climates",
        help_text="Rajasthan, Gujarat interior, Telangana plateau, interior Karnataka",
    )

    coastal_humid = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Suitable for Coastal & Humid Climates",
        help_text="Kerala coast, Mumbai, Chennai, Goa, Konkan, coastal Andhra/Odisha",
    )

    heavy_rainfall = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Suitable for Heavy Rainfall Regions",
        help_text="Kerala (2500mm+ annual rainfall), Northeast India, Western Ghats, Konkan",
    )

    cold_hilly = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Suitable for Cold & Hilly Regions",
        help_text="Himachal Pradesh, Uttarakhand, J&K, Sikkim, hill stations",
    )

    cyclone_prone = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name="Suitable for Cyclone-Prone Coastal Areas",
        help_text="Odisha coast, Tamil Nadu coast, Andhra coast (cyclone belt)",
    )

    # ─────────────────────────────────────────────
    # SECTION 5: REGIONAL AVAILABILITY
    # ─────────────────────────────────────────────

    seismic_zone = models.CharField(
        max_length=20,
        choices=SEISMIC_ZONE_CHOICES,
        blank=True,
        null=True,
        help_text="Minimum seismic zone this product is certified for. Leave blank if not relevant.",
    )

    # JSONField stores a Python list of state names.
    # Example: ["Kerala", "Tamil Nadu", "Karnataka", "Andhra Pradesh"]
    # Why list instead of ManyToMany with a State model?
    # → We don't need to query "which products are available in Kerala" from the State side.
    # → We only need to display availability on the product page.
    # → A simple list is far simpler to manage in admin and display in templates.
    # → ManyToMany would require a separate State table and junction table — overkill.
    states_available = models.JSONField(
        default=list,   # Same reason as specifications: default=list not default=[]
        blank=True,
        help_text="List of states where product is available. Example: [\"Kerala\", \"Tamil Nadu\"]",
    )

    regional_notes = models.TextField(
        blank=True,
        help_text="Special notes for specific regions. Example: 'Not recommended for high-altitude (>2000m) construction due to freeze-thaw cycles.'",
    )

    # ─────────────────────────────────────────────
    # SECTION 6: IMAGE
    # ─────────────────────────────────────────────

    # ImageField stores the FILE on disk and the FILE PATH in the database.
    # upload_to='products/' → saves to MEDIA_ROOT/products/ (i.e., media/products/)
    # Requires: Pillow library (already in requirements.txt)
    # blank=True, null=True → image is optional (use placeholder in template if missing)
    primary_image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        help_text="Main product image. Recommended: 800×800px square, max 2MB.",
    )

    # ─────────────────────────────────────────────
    # SECTION 7: PRICE PROVENANCE
    # ─────────────────────────────────────────────
    # These fields track WHERE the price came from and HOW reliable it is.
    # Critical for the Material Analyzer so users know whether a price is
    # a government-verified rate or just a seed estimate.

    price_source = models.CharField(
        max_length=50,
        choices=[
            ('pwd_sor', 'Kerala PWD Schedule of Rates'),
            ('data_gov', 'data.gov.in API'),
            ('admin', 'Admin Entered'),
            ('ai_estimate', 'AI Estimate'),
            ('seed_baseline', 'Seed Baseline'),
        ],
        default='seed_baseline',
        help_text="Where this price was sourced from.",
    )

    price_updated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the price was last verified/updated.",
    )

    price_confidence = models.CharField(
        max_length=10,
        choices=[('high', 'High'), ('medium', 'Medium'), ('low', 'Low')],
        default='low',
        help_text="Confidence in the price accuracy.",
    )

    price_source_reference = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text="Reference citation for this price (e.g., document name, URL).",
    )

    # ─────────────────────────────────────────────
    # SECTION 8: METADATA
    # ─────────────────────────────────────────────

    # SLUG EXPLAINED:
    # A slug is a URL-friendly version of the product name.
    # "UltraTech OPC 53 Grade Cement" → "ultratech-opc-53-grade-cement"
    #
    # Why slugs instead of IDs in URLs?
    # ID URL:   /materials/1247/      → Meaningless, bad for SEO
    # Slug URL: /materials/ultratech-opc-53-grade-cement/ → Google reads keywords, ranks higher
    #
    # unique=True means no two products can have the same slug.
    # Django will raise an error if you try to save a duplicate.
    # We handle duplicates in the save() method below.
    slug = models.SlugField(
        max_length=250,
        unique=True,
        blank=True,  # blank=True because we auto-generate it in save() — admin doesn't need to fill it
        help_text="Auto-generated URL identifier. Leave blank — generated from product name.",
    )

    # auto_now_add=True: set to current datetime ONCE when the row is first created. Never changes.
    # auto_now=True: set to current datetime EVERY TIME the row is saved (on every edit too).
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete pattern: instead of deleting from database (permanent, catastrophic),
    # set is_active=False to hide from users. The row stays in DB for audit/recovery.
    # All queries should filter: Product.objects.filter(is_active=True)
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Uncheck to hide product from the catalog without deleting it.",
    )

    # ─────────────────────────────────────────────
    # REVIEW AGGREGATE FIELDS
    # ─────────────────────────────────────────────
    # These are PRE-COMPUTED values updated by a signal whenever a review is saved.
    # WHY pre-compute instead of calculating on every page load?
    #
    # Without pre-computation (every page view):
    #   SELECT AVG(rating) FROM reviews WHERE product_id = ?
    #   → Scans every review row for this product on EVERY page view.
    #   → 10,000 reviews = 10,000 rows scanned × 1,000 users = 10 million row scans/hour.
    #   → Site becomes slow as reviews accumulate.
    #
    # With pre-computation (one update per new review):
    #   Just read product.average_rating → stored value, no calculation.
    #   → 1,000 users see same page → 1,000 × instant reads.
    #   → Site stays fast regardless of review count.
    #
    # Trade-off: data is written when a review is saved (rare), read on every page view (common).
    # Optimising for reads is almost always correct.
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.00,
    )

    total_reviews = models.IntegerField(default=0)

    # Stores the star breakdown: {"5": 120, "4": 45, "3": 10, "2": 5, "1": 2}
    # Used to render the rating histogram on the product detail page.
    rating_breakdown = models.JSONField(
        default=dict,
        blank=True,
    )

    # ─────────────────────────────────────────────
    # META & METHODS
    # ─────────────────────────────────────────────

    class Meta:
        db_table = 'products'       # Explicit table name (not Django's default 'products_product')
        ordering = ['category', 'name']   # Default order: grouped by category, alphabetical within
        indexes = [
            # Composite index: speeds up queries that filter by BOTH category AND is_active.
            # Example: Product.objects.filter(category='cement', is_active=True)
            # Without this: DB scans all active products, then filters by category.
            # With this: DB jumps directly to cement+active rows. Orders of magnitude faster.
            models.Index(fields=['category', 'is_active'], name='product_category_active_idx'),
        ]

    def __str__(self):
        # __str__ controls what Django shows in admin dropdowns, shell, etc.
        # "UltraTech OPC 53 Grade Cement (Cement)" is more useful than just the name.
        return f"{self.name} ({self.get_category_display()})"

    def save(self, *args, **kwargs):
        """
        Override Django's default save() to auto-generate slug before saving.

        HOW SLUG AUTO-GENERATION WORKS:
        1. If this is a new product (no slug yet): generate from name.
        2. If slug already exists (editing existing product): keep it.
           Reason: Changing slug = broken URLs. Google loses ranking. Bad.

        slugify() is a Django utility that:
        - Converts to lowercase
        - Replaces spaces with hyphens
        - Removes special characters (brackets, slashes, etc.)

        Example:
          slugify("UltraTech OPC 53 Grade Cement") → "ultratech-opc-53-grade-cement"
          slugify("Asian Paints - Apcolite (Premium)")→ "asian-paints-apcolite-premium"

        HANDLING DUPLICATE SLUGS:
        Two products named "Standard Cement" would both generate slug "standard-cement".
        But slug must be unique. So we append a number: "standard-cement-2", "standard-cement-3".
        """
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 2
            # Keep trying until we find a slug that doesn't exist.
            # Check excludes current instance (in case of edit) via pk comparison.
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        # Call the parent save() — this is what actually writes to the database.
        # Always call super().save() at the end, otherwise the row never saves.
        super().save(*args, **kwargs)

    @property
    def climate_badges(self):
        """
        Returns a list of dicts describing which climates this product is suitable for.
        Used in templates to display the ✓/✗ climate badges.

        WHY a property instead of doing this logic in the template?
        - Template logic should be minimal (display only)
        - Business logic (what counts as a "badge") belongs in the model
        - Property is reusable across multiple templates
        - Easier to test

        Returns: list of {label, suitable, description} dicts.
        Template iterates this to render badges.
        """
        return [
            {
                'key': 'hot_dry',
                'label': 'Hot & Dry',
                'suitable': self.hot_dry,
                'description': 'Rajasthan, Gujarat, interior Karnataka, Telangana',
            },
            {
                'key': 'coastal_humid',
                'label': 'Coastal & Humid',
                'suitable': self.coastal_humid,
                'description': 'Kerala coast, Mumbai, Chennai, Goa, Konkan',
            },
            {
                'key': 'heavy_rainfall',
                'label': 'Heavy Rainfall',
                'suitable': self.heavy_rainfall,
                'description': 'Kerala, Northeast India, Western Ghats',
            },
            {
                'key': 'cold_hilly',
                'label': 'Cold & Hilly',
                'suitable': self.cold_hilly,
                'description': 'Himachal, Uttarakhand, J&K, hill stations',
            },
            {
                'key': 'cyclone_prone',
                'label': 'Cyclone-Prone Coast',
                'suitable': self.cyclone_prone,
                'description': 'Odisha coast, Tamil Nadu coast, Andhra coast',
            },
        ]

    @property
    def suitable_climates(self):
        """Returns list of climate labels this product IS suitable for."""
        return [b['label'] for b in self.climate_badges if b['suitable']]

    @property
    def unsuitable_climates(self):
        """Returns list of climate labels this product is NOT suitable for."""
        return [b['label'] for b in self.climate_badges if not b['suitable']]

    @property
    def primary_image_url(self):
        """Returns the URL of the primary image, or the first image, or None."""
        img = self.images.filter(is_primary=True).first()
        if not img:
            img = self.images.first()
        return img.image_url if img else None

    @property
    def price_display(self):
        """Human-readable price string. Example: '₹385 / bag'"""
        return f"₹{self.price:,.0f} / {self.unit}"

    @property
    def mrp_display(self):
        """Human-readable MRP string. Example: 'MRP ₹400 / bag'"""
        return f"MRP ₹{self.mrp:,.0f} / {self.unit}"


class ProductImage(models.Model):
    """
    Stores multiple images per product as external URLs.

    WHY external URLs instead of uploaded files?
    - No disk storage needed on the server
    - Images load directly from manufacturer/CDN servers
    - Easy to update: just change the URL in admin
    - For a presentation/demo: zero setup, just seed and run

    Each product can have multiple images. One is marked is_primary=True
    which appears on the product list card. All images appear in the
    detail page gallery carousel.
    """

    product = models.ForeignKey(
        Product,
        related_name='images',
        on_delete=models.CASCADE,
    )

    image_url = models.URLField(
        max_length=1000,
        help_text="Direct URL to the image. Must be publicly accessible.",
    )

    caption = models.CharField(
        max_length=200,
        blank=True,
        help_text="Optional caption. Example: 'Front view', 'Application on wall'",
    )

    is_primary = models.BooleanField(
        default=False,
        help_text="Shown on product list cards. Only one image per product should be primary.",
    )

    sort_order = models.PositiveSmallIntegerField(
        default=0,
        help_text="Lower number = shown first in gallery.",
    )

    class Meta:
        db_table = 'product_images'
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f"{self.product.name} — image {self.sort_order + 1}"


class ViewHistory(models.Model):
    """Tracks which products a logged-in user has viewed. One row per user+product pair."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='view_history',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='views',
    )
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'view_history'
        unique_together = ('user', 'product')
        ordering = ['-viewed_at']

    def __str__(self):
        return f"{self.user.email} viewed {self.product.name}"


class SavedMaterial(models.Model):
    """Wishlist — materials a logged-in user has bookmarked."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_materials',
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='saved_by',
    )
    saved_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'saved_materials'
        unique_together = ('user', 'product')
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.email} saved {self.product.name}"
