"""
apps/users/models.py — The core data models for all users in OurHome.

HOW DJANGO MODELS WORK:
- Each class that inherits from models.Model becomes a DATABASE TABLE.
- Each class attribute (like email, phone) becomes a COLUMN in that table.
- Django automatically creates SQL and manages the database for you.
- When you change a model, you run "makemigrations" to generate a migration file,
  then "migrate" to apply it to the database.

WHY AbstractUser?
- Django comes with a built-in User model (username, password, email, etc.)
- AbstractUser gives us ALL of those fields for free, and we ADD our own on top.
- The alternative, AbstractBaseUser, would require writing everything from scratch.
- Rule of thumb: Use AbstractUser unless you need to completely redesign authentication.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class User(AbstractUser):
    """
    Custom user model for OurHome.

    INHERITED FROM AbstractUser (we get these for FREE):
    - username, password, first_name, last_name, email
    - is_staff, is_active, is_superuser, date_joined, last_login

    WE ADD:
    - phone, user_type, profile_photo, bio, date_of_birth
    - city, district, state, pincode (for location-based material suggestions)
    """

    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('contractor', 'Contractor'),
        ('architect', 'Architect'),
        ('interior_designer', 'Interior Designer'),
    ]

    # Phone number validator — a RegexValidator checks the value against a pattern
    # ^ = start, \+? = optional +, 1? = optional 1, \d{9,15} = 9 to 15 digits, $ = end
    # If the value doesn't match, Django shows the error message.
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be 9-15 digits. Can start with +."
    )

    # ---- Core fields ----
    # unique=True means no two users can have the same email
    email = models.EmailField(unique=True)

    # validators=[phone_regex] runs our regex check before saving
    # blank=True means the form field can be left empty
    # null=True means the database column can store NULL
    phone = models.CharField(
        validators=[phone_regex],
        max_length=15,
        unique=True,
        blank=True,
        null=True,
    )

    # choices=USER_TYPE_CHOICES creates a dropdown in forms and admin
    # default='customer' means new users are customers unless specified otherwise
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='customer',
    )

    # ---- Profile fields (common to all users) ----
    # ImageField stores an image file. upload_to tells Django WHERE to save it.
    # %Y/%m creates folders by year/month (e.g., media/profile_photos/2026/02/)
    # Requires Pillow package to work.
    profile_photo = models.ImageField(
        upload_to='profile_photos/%Y/%m/',
        blank=True,
        null=True,
    )

    banner_image = models.ImageField(
        upload_to='user_banners/',
        blank=True,
        null=True,
        help_text='Profile banner image (recommended: 1400×350px)',
    )

    # TextField for longer text (no max length in DB, but we limit in the form)
    bio = models.TextField(max_length=500, blank=True)

    # DateField stores a date (no time). Used for age verification, etc.
    date_of_birth = models.DateField(blank=True, null=True)

    # ---- Location fields ----
    # These help suggest materials suitable for the user's region/climate.
    # We ask for approximate location (city/district), NOT exact address.
    city = models.CharField(max_length=100, blank=True)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, default='Kerala')
    pincode = models.CharField(max_length=10, blank=True)

    # USERNAME_FIELD = which field is used to LOG IN
    # We use email instead of the default username.
    USERNAME_FIELD = 'email'

    # REQUIRED_FIELDS = extra fields asked when running "createsuperuser" command.
    # email is already required because it's USERNAME_FIELD.
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'users'  # Explicit table name instead of Django's default 'users_user'

    def __str__(self):
        return self.email

    @property
    def is_service_provider(self):
        """Returns True if this user is a contractor, architect, or interior designer."""
        return self.user_type in ('contractor', 'architect', 'interior_designer')

    @property
    def is_customer(self):
        """Returns True if this user is a regular customer."""
        return self.user_type == 'customer'

    @property
    def full_name(self):
        """Returns 'First Last' or falls back to email if no name set."""
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.email

    @property
    def is_profile_complete(self):
        """
        Check if the user has filled in minimum required profile info.
        Used to redirect incomplete profiles to the 'complete profile' page.
        """
        base_complete = bool(self.first_name and self.phone and self.city)
        if self.is_service_provider:
            # Service providers also need their professional profile filled in
            return base_complete and hasattr(self, 'service_provider_profile')
        return base_complete


class ServiceProviderProfile(models.Model):
    """
    Professional profile for contractors, architects, and interior designers.

    WHY A SEPARATE MODEL (not just more fields on User)?

    1. NOT ALL USERS ARE PROVIDERS. If we put 15+ provider fields on the User table,
       every customer row wastes space with empty columns.

    2. SEPARATION OF CONCERNS. User handles authentication (login/password).
       ServiceProviderProfile handles business info (experience, pricing, verification).

    3. ONE-TO-ONE RELATIONSHIP. Each User has AT MOST one ServiceProviderProfile.
       Access it via: user.service_provider_profile

    4. VERIFICATION WORKFLOW. Only providers go through admin verification.
       Keeping it separate makes this logic cleaner.
    """

    VERIFICATION_STATUS_CHOICES = [
        ('pending', 'Pending Review'),       # Just signed up, waiting for admin
        ('under_review', 'Under Review'),    # Admin is looking at their documents
        ('approved', 'Approved'),            # Verified, visible on the platform
        ('rejected', 'Rejected'),            # Documents didn't check out
    ]

    SPECIALIZATION_CHOICES = [
        # Contractor specializations
        ('residential', 'Residential Construction'),
        ('commercial', 'Commercial Construction'),
        ('renovation', 'Renovation'),
        ('interior_work', 'Interior Work'),
        ('eco_friendly', 'Eco-Friendly Building'),
        ('smart_home', 'Smart Home'),
        ('traditional', 'Traditional Kerala Style'),
        ('modern', 'Modern Architecture'),
        ('luxury', 'Luxury Villas'),
        # Architect specializations
        ('structural', 'Structural Design'),
        ('landscape', 'Landscape Architecture'),
        ('urban_planning', 'Urban Planning'),
        # Interior Designer specializations
        ('minimalist', 'Minimalist Design'),
        ('contemporary', 'Contemporary'),
        ('classic', 'Classic'),
        ('sustainable', 'Sustainable Design'),
    ]

    # ---- Link to User ----
    # OneToOneField = this profile belongs to EXACTLY ONE user.
    # on_delete=CASCADE means: if the User is deleted, delete this profile too.
    # related_name='service_provider_profile' means: user.service_provider_profile gives you this object.
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='service_provider_profile',
    )

    # ---- Profile visuals ----
    banner_image = models.ImageField(
        upload_to='provider_banners/',
        blank=True,
        null=True,
        help_text='Profile banner image (recommended: 1400×350px)',
    )

    # ---- Business info ----
    business_name = models.CharField(max_length=200)
    years_of_experience = models.PositiveIntegerField(default=0)
    total_projects_completed = models.PositiveIntegerField(default=0)
    typical_project_duration = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., '6-12 months', '2-4 weeks'",
    )

    # JSONField stores a Python list/dict as JSON in the database.
    # Perfect for a list of specialization codes like ['residential', 'eco_friendly'].
    # We use this instead of ManyToManyField because the options are predefined and simple.
    specializations = models.JSONField(
        default=list,
        blank=True,
        help_text="List of specialization codes",
    )

    # ---- Pricing ----
    # DecimalField is used for money (not FloatField, which has rounding errors).
    # max_digits=10, decimal_places=2 means up to 99,999,999.99
    price_range_min = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )
    price_range_max = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True,
    )
    price_unit = models.CharField(
        max_length=20,
        default='per sqft',
        help_text="e.g., 'per sqft', 'per project', 'per hour'",
    )

    # ---- Contact & location ----
    office_address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    whatsapp_number = models.CharField(max_length=15, blank=True)

    # ---- Verification ----
    verification_status = models.CharField(
        max_length=20,
        choices=VERIFICATION_STATUS_CHOICES,
        default='pending',
    )
    verification_notes = models.TextField(
        blank=True,
        help_text="Admin notes about the verification decision",
    )
    verified_at = models.DateTimeField(null=True, blank=True)

    # ---- Verification documents ----
    # FileField stores any file type (PDF, images, etc.)
    # upload_to organizes files into folders by year/month.
    id_proof = models.FileField(
        upload_to='verification_docs/id_proofs/%Y/%m/',
        blank=True,
        help_text="Government ID (Aadhaar, PAN, etc.)",
    )
    license_document = models.FileField(
        upload_to='verification_docs/licenses/%Y/%m/',
        blank=True,
        help_text="Professional license, registration certificate, etc.",
    )
    portfolio_document = models.FileField(
        upload_to='verification_docs/portfolios/%Y/%m/',
        blank=True,
        help_text="Portfolio PDF or work samples",
    )

    # ---- Verification actor ----
    # Which admin user approved/rejected this provider.
    # SET_NULL: if the admin account is deleted, the approval record stays.
    verified_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='verified_providers',
        help_text="Admin user who approved or rejected this provider",
    )

    # ---- Timestamps ----
    # auto_now_add=True: set to current time when the row is CREATED (never changes)
    # auto_now=True: set to current time every time the row is SAVED (updates on edit)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'service_provider_profiles'

    def __str__(self):
        return f"{self.business_name} ({self.user.email})"

    @property
    def is_verified(self):
        """Returns True only if admin has approved this provider."""
        return self.verification_status == 'approved'

    @property
    def price_range_display(self):
        """Human-readable price range string for templates."""
        if self.price_range_min and self.price_range_max:
            return f"₹{self.price_range_min:,.0f} – {self.price_range_max:,.0f} {self.price_unit}"
        return "Contact for pricing"


class PortfolioImage(models.Model):
    """
    A project photo uploaded by a service provider to their public profile.

    WHY SEPARATE FROM ServiceProviderProfile?
    - A provider can have MANY portfolio images (one-to-many).
    - Storing them as a separate model lets us add metadata per image
      (title, type, date) and order/filter them easily.
    - Providers upload via the dashboard; visitors see them on the public profile.
    """

    PROJECT_TYPE_CHOICES = [
        ('residential',  'Residential'),
        ('commercial',   'Commercial'),
        ('industrial',   'Industrial'),
        ('renovation',   'Renovation'),
    ]

    BUDGET_RANGE_CHOICES = [
        ('budget',   'Budget (< ₹20L)'),
        ('mid',      'Mid-range (₹20–50L)'),
        ('premium',  'Premium (₹50L–1Cr)'),
        ('luxury',   'Luxury (> ₹1Cr)'),
    ]

    # Links to the User (provider), not ServiceProviderProfile directly.
    # This keeps portfolio queries simple: request.user.portfolio_images.all()
    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='portfolio_images',
    )

    project_title = models.CharField(max_length=200)
    project_description = models.TextField(blank=True)
    project_location = models.CharField(max_length=200, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    project_type = models.CharField(
        max_length=50,
        choices=PROJECT_TYPE_CHOICES,
        default='residential',
    )
    project_size = models.CharField(
        max_length=100,
        blank=True,
        help_text="e.g., '2500 sq ft', '4 BHK villa'",
    )
    budget_range = models.CharField(
        max_length=50,
        choices=BUDGET_RANGE_CHOICES,
        blank=True,
    )

    # ImageField stores files under media/portfolio/YYYY/MM/
    # Requires Pillow to be installed.
    image = models.ImageField(upload_to='portfolio/%Y/%m/')

    # featured=True images appear in the "highlights" grid on the public profile.
    featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'portfolio_images'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.project_title} — {self.provider.email}"


class ServiceInquiry(models.Model):
    """
    A contact form submission sent to a service provider through their public profile.

    DESIGN DECISION — no login required:
    - Potential clients (homeowners) may not have an OurHome account yet.
    - Requiring signup would create friction and reduce leads for providers.
    - We store sender details directly on the inquiry record.

    PRIVACY:
    - Only the provider and admins can view inquiries (enforced in the view/admin).
    - Sender's contact info is never displayed publicly.
    """

    provider = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='received_inquiries',
    )

    sender_name = models.CharField(max_length=200)
    sender_email = models.EmailField()
    sender_phone = models.CharField(max_length=15, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'service_inquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f"Inquiry from {self.sender_name} → {self.provider.email}"
