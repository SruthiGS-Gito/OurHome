"""
apps/users/forms.py — All forms used in the users app.

HOW DJANGO FORMS WORK:
- A Form class defines WHAT FIELDS a form has and HOW TO VALIDATE them.
- When the user submits a form, Django creates a form instance with the POST data.
- form.is_valid() runs all validators and returns True/False.
- form.cleaned_data gives you the validated, clean data as a Python dictionary.
- form.errors gives you any validation error messages.

TWO TYPES OF FORMS:
1. forms.Form — You define every field manually. Used when the form doesn't map to a model.
2. forms.ModelForm — Auto-generates fields from a model. Used for create/edit forms.

WHY EXTEND ALLAUTH'S SignupForm?
- allauth's SignupForm already handles: email uniqueness, password strength validation,
  CSRF protection, email verification token generation.
- We extend it to ADD our custom fields (phone, name, user_type) on top.
- If we built from scratch, we'd have to re-implement all that security logic.
"""

from django import forms
from allauth.account.forms import SignupForm
from .models import User, ServiceProviderProfile, PortfolioImage


class CustomerSignupForm(SignupForm):
    """
    Signup form for CUSTOMERS (people browsing for materials/contractors).

    This form is set as the default signup form in settings.py:
        ACCOUNT_FORMS = {'signup': 'apps.users.forms.CustomerSignupForm'}

    allauth automatically uses this form at /accounts/signup/.
    """

    # forms.CharField = a text input field
    # widget = controls the HTML element that renders
    # attrs = HTML attributes added to the element
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'First name',
            'class': 'form-input',  # Matches our existing CSS class
        }),
    )

    last_name = forms.CharField(
        max_length=150,
        required=False,  # Last name is optional
        widget=forms.TextInput(attrs={
            'placeholder': 'Last name',
            'class': 'form-input',
        }),
    )

    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': '+91 98765 43210',
            'class': 'form-input',
        }),
    )

    # HiddenInput = this field exists but the user doesn't see it.
    # Customer signup always creates a 'customer' user.
    user_type = forms.ChoiceField(
        choices=[('customer', 'Customer')],
        initial='customer',
        widget=forms.HiddenInput(),
    )

    def save(self, request):
        """
        Called by allauth when creating a new user.

        HOW THIS WORKS:
        1. super().save(request) calls allauth's save method, which creates the User
           with email and password, and sends the verification email.
        2. We then return the user object.
        3. Our AccountAdapter.save_user() (in adapters.py) handles setting the
           extra fields (first_name, phone, user_type) on the user.
        """
        user = super().save(request)
        return user


class ServiceProviderSignupForm(SignupForm):
    """
    Signup form for SERVICE PROVIDERS (contractors, architects, designers).

    This form is NOT set as the default — it's used at a separate URL (/provider/signup/).
    It collects both account info AND initial business info.
    """

    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'First name',
            'class': 'form-input',
        }),
    )

    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'placeholder': 'Last name',
            'class': 'form-input',
        }),
    )

    phone = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'placeholder': '+91 98765 43210',
            'class': 'form-input',
        }),
    )

    # ChoiceField = dropdown menu. The user selects their professional category.
    user_type = forms.ChoiceField(
        choices=[
            ('contractor', 'Contractor'),
            ('architect', 'Architect'),
            ('interior_designer', 'Interior Designer'),
        ],
        widget=forms.Select(attrs={'class': 'form-input'}),
    )

    # Business info collected during signup
    business_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': 'Your business or company name',
            'class': 'form-input',
        }),
    )

    years_of_experience = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={
            'placeholder': 'Years of experience',
            'class': 'form-input',
        }),
    )

    def save(self, request):
        """
        Creates the User AND the ServiceProviderProfile in one step.

        After this:
        1. User account is created (but email not yet verified)
        2. ServiceProviderProfile is created with status='pending'
        3. allauth sends the verification email
        4. After verifying, the provider is redirected to complete their profile
        """
        user = super().save(request)

        # Create the provider profile linked to this user
        ServiceProviderProfile.objects.create(
            user=user,
            business_name=self.cleaned_data['business_name'],
            years_of_experience=self.cleaned_data['years_of_experience'],
            verification_status='pending',
        )
        return user


class UserProfileForm(forms.ModelForm):
    """
    Form for editing basic profile info (used by ALL user types).

    ModelForm MAGIC:
    - class Meta tells Django which model and fields to use.
    - Django auto-generates the form fields from the model field definitions.
    - On save(), it updates the database row automatically.
    - You don't write a single SQL query.
    """

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone', 'profile_photo', 'banner_image',
            'bio', 'date_of_birth', 'city', 'district', 'state', 'pincode',
        ]
        widgets = {
            # type='date' renders a date picker in the browser
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'city': forms.TextInput(attrs={'class': 'form-input'}),
            'district': forms.TextInput(attrs={'class': 'form-input'}),
            'state': forms.TextInput(attrs={'class': 'form-input'}),
            'pincode': forms.TextInput(attrs={'class': 'form-input'}),
            # Plain FileInput (no "Currently: …" text, no clear checkbox).
            # Visually hidden — triggered via a styled <label> in the template.
            'profile_photo': forms.FileInput(attrs={
                'accept': 'image/*',
                'style': 'display:none;',
            }),
            'banner_image': forms.FileInput(attrs={
                'id': 'id_banner_image',
                'accept': 'image/*',
                'style': 'display:none;',
            }),
        }


class ServiceProviderProfileForm(forms.ModelForm):
    """
    Form for editing service provider-specific business info.

    Used on the profile edit page for contractors/architects/designers.
    This form is shown IN ADDITION to UserProfileForm (they edit both together).
    """

    class Meta:
        model = ServiceProviderProfile
        fields = [
            'banner_image',
            'business_name', 'years_of_experience', 'total_projects_completed',
            'typical_project_duration', 'specializations',
            'price_range_min', 'price_range_max', 'price_unit',
            'office_address', 'website', 'whatsapp_number',
            'id_proof', 'license_document', 'portfolio_document',
        ]
        widgets = {
            'business_name': forms.TextInput(attrs={'class': 'form-input'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-input'}),
            'total_projects_completed': forms.NumberInput(attrs={'class': 'form-input'}),
            'typical_project_duration': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., 6-12 months',
            }),
            'price_range_min': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Min price'}),
            'price_range_max': forms.NumberInput(attrs={'class': 'form-input', 'placeholder': 'Max price'}),
            'price_unit': forms.TextInput(attrs={'class': 'form-input'}),
            'office_address': forms.Textarea(attrs={'rows': 2, 'class': 'form-input'}),
            'website': forms.URLInput(attrs={'class': 'form-input', 'placeholder': 'https://'}),
            'whatsapp_number': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+91...'}),
        }


class PortfolioImageForm(forms.ModelForm):
    """
    Form for uploading a single portfolio project image.
    Used on the provider dashboard to add new project photos.
    """

    class Meta:
        model = PortfolioImage
        fields = [
            'image', 'project_title', 'project_description',
            'project_location', 'completion_date', 'project_type',
            'project_size', 'budget_range', 'featured',
        ]
        widgets = {
            'project_title': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'e.g., Luxury Villa in Thrissur',
            }),
            'project_description': forms.Textarea(attrs={
                'class': 'form-input', 'rows': 3,
                'placeholder': 'Brief description of the project…',
            }),
            'project_location': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'e.g., Thrissur, Kerala',
            }),
            'completion_date': forms.DateInput(attrs={
                'class': 'form-input', 'type': 'date',
            }),
            'project_type': forms.Select(attrs={'class': 'form-input'}),
            'project_size': forms.TextInput(attrs={
                'class': 'form-input', 'placeholder': 'e.g., 2500 sq ft',
            }),
            'budget_range': forms.Select(attrs={'class': 'form-input'}),
        }
