"""
apps/users/views.py — All views (page handlers) for the users app.

HOW DJANGO VIEWS WORK:
- A "view" is a Python function that receives an HTTP request and returns an HTTP response.
- When a user visits a URL (e.g., /dashboard/), Django looks up which view handles that URL
  (defined in urls.py) and calls that function.
- The view typically: validates input → queries the database → renders a template → returns HTML.

THE REQUEST-RESPONSE CYCLE:
    Browser → URL → urls.py → view function → template → HTML → Browser

DECORATORS USED:
- @login_required: If the user isn't logged in, redirect them to the login page.
  Without this, anyone could visit /dashboard/ or /profile/ without being authenticated.

HTMX PATTERN:
- When request.htmx is True, the request came from HTMX (JavaScript that sends AJAX requests).
- Instead of returning a FULL page, we return just a small HTML fragment.
- HTMX swaps that fragment into the page — no full page reload needed.
- This makes the app feel fast and smooth, like a mobile app.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q as DQ, Case, When, IntegerField
from allauth.account.utils import complete_signup
from allauth.account import app_settings as allauth_settings

from .models import User, ServiceProviderProfile, PortfolioImage, ServiceInquiry
from apps.products.models import Product
from .forms import (
    UserProfileForm,
    ServiceProviderProfileForm,
    ServiceProviderSignupForm,
    PortfolioImageForm,
)


@login_required
def dashboard_view(request):
    """
    Main dashboard — the first page users see after logging in.

    WHAT IT DOES:
    1. Gets the currently logged-in user from request.user
    2. If the user is a service provider, also loads their business profile
    3. Renders different dashboard content based on user type

    WHY ONE VIEW FOR BOTH USER TYPES?
    - Keeps the URL simple (/dashboard/ for everyone)
    - The template uses {% if user.is_service_provider %} to show different sections
    - If dashboards grow too different later, we can split into separate views

    URL: /dashboard/
    TEMPLATE: templates/users/dashboard.html
    """
    context = {
        'user': request.user,
    }

    if request.user.is_service_provider:
        try:
            # user.service_provider_profile works because of the related_name
            # set in the OneToOneField in ServiceProviderProfile model
            context['provider_profile'] = request.user.service_provider_profile
        except ServiceProviderProfile.DoesNotExist:
            # Provider signed up but profile was never created — redirect to complete it
            return redirect('profile_complete')
        # Featured images first, then newest — used by the portfolio grid in the template
        context['portfolio_images'] = request.user.portfolio_images.order_by('-featured', '-created_at')
    else:
        # Homeowner — real activity counts and info card data
        from apps.products.models import ViewHistory, SavedMaterial
        from .models import ServiceInquiry

        context['materials_browsed'] = ViewHistory.objects.filter(user=request.user).count()
        context['saved_count'] = SavedMaterial.objects.filter(user=request.user).count()
        context['last_saved'] = list(
            SavedMaterial.objects
            .filter(user=request.user)
            .select_related('product')[:2]
        )
        context['inquiry_count'] = ServiceInquiry.objects.filter(
            sender_email=request.user.email
        ).count()

        # Climate zone: default to Coastal & Humid for Kerala users
        state = getattr(request.user, 'state', 'Kerala') or 'Kerala'
        context['climate_zone'] = 'Coastal & Humid' if 'Kerala' in state else state

        recent_views = list(
            ViewHistory.objects
            .filter(user=request.user)
            .select_related('product')[:10]
        )
        context['recent_views'] = recent_views
        # Fall back to popular products if no history yet
        if recent_views:
            context['popular_products'] = [v.product for v in recent_views]
        else:
            context['popular_products'] = list(
                Product.objects.filter(is_active=True).order_by('-total_reviews')[:10]
            )
        context['recommended_products'] = _get_recommendations(request.user, limit=4)

    return render(request, 'users/dashboard.html', context)


@login_required
def profile_view(request):
    """
    View your own profile.

    URL: /profile/
    TEMPLATE: templates/users/profile.html
    """
    context = {'profile_user': request.user}

    if request.user.is_service_provider:
        try:
            context['provider_profile'] = request.user.service_provider_profile
        except ServiceProviderProfile.DoesNotExist:
            pass

    return render(request, 'users/profile.html', context)


@login_required
def profile_edit_view(request):
    """
    Edit your own profile. Supports HTMX for no-reload form submission.

    HOW THIS VIEW HANDLES BOTH GET AND POST:
    - GET request (user visits the page): Show the form pre-filled with current data
    - POST request (user submits the form): Validate and save the data

    HTMX INTEGRATION:
    - The form has hx-post="/profile/edit/" hx-target="#profile-form"
    - On submit, HTMX sends a POST request with HX-Request header
    - This view detects request.htmx and returns ONLY the form partial
    - HTMX swaps just the form section — no full page reload
    - If there are errors, the partial includes error messages
    - If successful, the partial shows a success message

    SECURITY:
    - @login_required ensures only authenticated users can access this
    - We ALWAYS edit request.user — never accept a user ID parameter
    - This means you can ONLY edit your OWN profile, never someone else's

    URL: /profile/edit/
    TEMPLATE: templates/users/profile_edit.html
    PARTIAL: templates/users/partials/profile_form.html (for HTMX responses)
    """
    user = request.user

    if request.method == 'POST':
        # Create form instances with the submitted data (request.POST) and files (request.FILES)
        # instance=user tells ModelForm to UPDATE this existing user, not create a new one
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        provider_form = None

        if user.is_service_provider:
            # get_or_create: if the profile exists, get it; if not, create a blank one
            profile, _ = ServiceProviderProfile.objects.get_or_create(
                user=user,
                defaults={'business_name': user.full_name},
            )
            provider_form = ServiceProviderProfileForm(
                request.POST, request.FILES, instance=profile,
            )

        # Validate all forms
        forms_valid = form.is_valid()
        if provider_form:
            forms_valid = forms_valid and provider_form.is_valid()

        if forms_valid:
            form.save()
            if provider_form:
                provider_form.save()
            messages.success(request, 'Profile updated successfully!')

            # HTMX: return only the form partial (not the full page)
            if request.htmx:
                return render(request, 'users/partials/profile_form.html', {
                    'form': form,
                    'provider_form': provider_form,
                    'success': True,
                })

            # For normal requests, reload edit page with success message
            form = UserProfileForm(instance=user)
            provider_form = ServiceProviderProfileForm(instance=profile) if user.is_service_provider else None

            return render(request, 'users/profile_edit.html', {
                'form': form,
                'provider_form': provider_form,
            'success': True
            })
        else:
            # Validation failed — show errors
            if request.htmx:
                return render(request, 'users/partials/profile_form.html', {
                    'form': form,
                    'provider_form': provider_form,
                })
    else:
        # GET request — show the form with current data
        form = UserProfileForm(instance=user)
        provider_form = None
        if user.is_service_provider:
            profile, _ = ServiceProviderProfile.objects.get_or_create(
                user=user,
                defaults={'business_name': user.full_name},
            )
            provider_form = ServiceProviderProfileForm(instance=profile)

    return render(request, 'users/profile_edit.html', {
        'form': form,
        'provider_form': provider_form,
    })


def public_profile_view(request, user_id):
    """
    Legacy URL /provider/<user_id>/ — permanently redirects to the typed
    profile URL (/contractor/<username>/, /architect/<username>/, etc.).
    """
    user = get_object_or_404(User, pk=user_id, is_active=True)
    type_map = {
        'contractor':        'contractor',
        'architect':         'architect',
        'interior_designer': 'designer',
    }
    url_type = type_map.get(user.user_type)
    if url_type:
        return redirect(f'/{url_type}/{user.username}/', permanent=True)
    return redirect('/')


def service_provider_signup_view(request):
    """
    Separate signup page for service providers (contractors, architects, designers).

    WHY SEPARATE FROM CUSTOMER SIGNUP?
    - Service providers need MORE fields (business name, experience, professional type)
    - They go through a DIFFERENT flow after signup (verify email → complete profile → wait for admin approval)
    - Mixing both flows into one form would be confusing

    POST-SIGNUP FLOW:
    1. Provider fills form → account created with verification_status='pending'
    2. allauth sends verification email
    3. Provider clicks email link → email verified
    4. Provider logs in → redirected to /profile/complete/ (by our adapter)
    5. Provider fills in remaining details + uploads documents
    6. Admin reviews and approves/rejects in /admin/

    URL: /provider/signup/
    TEMPLATE: templates/users/provider_signup.html
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ServiceProviderSignupForm(request.POST)
        if form.is_valid():
            user = form.save(request)
            # complete_signup logs the user in immediately (no email verification)
            # and redirects to get_login_redirect_url (→ /profile/complete/ for new providers)
            return complete_signup(
                request, user,
                allauth_settings.EMAIL_VERIFICATION,
                '/profile/complete/',
            )
    else:
        form = ServiceProviderSignupForm()

    return render(request, 'users/provider_signup.html', {'form': form})


@login_required
def profile_complete_view(request):
    """
    Shown to service providers who haven't completed their professional profile.

    They must fill in:
    - Business details (experience, projects, specializations)
    - Pricing information
    - Upload verification documents (ID proof, license, portfolio)

    After submission, status stays 'pending' until admin approves.

    URL: /profile/complete/
    TEMPLATE: templates/users/profile_complete.html
    """
    if not request.user.is_service_provider:
        return redirect('dashboard')

    profile, created = ServiceProviderProfile.objects.get_or_create(
        user=request.user,
        defaults={'business_name': request.user.full_name},
    )

    if request.method == 'POST':
        form = ServiceProviderProfileForm(
            request.POST, request.FILES, instance=profile,
        )
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Profile submitted for verification! '
                'We will review it within 2-3 business days.',
            )
            return redirect('dashboard')
    else:
        form = ServiceProviderProfileForm(instance=profile)

    return render(request, 'users/profile_complete.html', {'form': form})


def search_view(request):
    """
    Search across service providers (and later, materials).

    HTMX LIVE SEARCH:
    - The search input in base.html has hx-get="/search/" hx-trigger="keyup changed delay:300ms"
    - As the user types, HTMX sends a GET request after 300ms of no typing
    - This view detects request.htmx and returns only the search results partial
    - Results appear below the search box without a page reload

    delay:300ms = wait 300 milliseconds after the user stops typing before sending.
    This prevents sending a request for every single keystroke (debouncing).

    URL: /search/
    TEMPLATE: templates/search.html
    PARTIAL: templates/partials/search_results.html (for HTMX responses)
    """
    query = request.GET.get('q', '').strip()

    context = {
        'query': query,
        'products': [],
        'contractors': [],
        'architects': [],
        'designers': [],
        'total_count': 0,
    }

    is_htmx = hasattr(request, 'htmx') and request.htmx

    if query:
        if is_htmx:
            # Dropdown: name/brand/category only — no description to avoid
            # false positives (e.g. cement appearing in "steel" searches).
            # Ordered by field priority: name match first, then brand, then category.
            context['products'] = list(
                Product.objects.filter(
                    is_active=True
                ).filter(
                    DQ(name__icontains=query) |
                    DQ(brand__icontains=query) |
                    DQ(category__icontains=query)
                ).annotate(
                    relevance=Case(
                        When(name__icontains=query, then=1),
                        When(brand__icontains=query, then=2),
                        When(category__icontains=query, then=3),
                        default=4,
                        output_field=IntegerField(),
                    )
                ).order_by('relevance', 'name').distinct()[:5]
            )
        else:
            # Full search page: include description for thorough results,
            # ordered by review count so popular products surface first.
            context['products'] = list(
                Product.objects.filter(
                    is_active=True
                ).filter(
                    DQ(name__icontains=query) |
                    DQ(brand__icontains=query) |
                    DQ(description__icontains=query) |
                    DQ(category__icontains=query)
                ).distinct().order_by('-total_reviews')[:5]
            )

        # Search through approved AND pending providers
        # select_related('user') loads the linked User in the same DB query
        # (instead of making a separate query for each provider — this is called N+1 prevention)
        providers = ServiceProviderProfile.objects.filter(
            verification_status__in=['approved', 'pending'],
        ).select_related('user')

        provider_q = (
            DQ(business_name__icontains=query) |
            DQ(user__first_name__icontains=query) |
            DQ(user__last_name__icontains=query) |
            DQ(user__city__icontains=query)
        )

        context['contractors'] = providers.filter(
            user__user_type='contractor',
        ).filter(provider_q)[:8]

        context['architects'] = providers.filter(
            user__user_type='architect',
        ).filter(provider_q)[:8]

        context['designers'] = providers.filter(
            user__user_type='interior_designer',
        ).filter(provider_q)[:8]

        context['total_count'] = (
            len(context['products'])
            + len(context['contractors'])
            + len(context['architects'])
            + len(context['designers'])
        )

    # HTMX: return only the results fragment
    if is_htmx:
        return render(request, 'partials/search_results.html', context)

    return render(request, 'search.html', context)


# ══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATION HELPERS
# ══════════════════════════════════════════════════════════════════════════════

# Maps keywords found in user.state → Product climate boolean field name
_STATE_CLIMATE_MAP = {
    # Coastal & humid
    'kerala':        'coastal_humid',
    'goa':           'coastal_humid',
    'lakshadweep':   'coastal_humid',
    # Hot & dry
    'rajasthan':     'hot_dry',
    'gujarat':       'hot_dry',
    'haryana':       'hot_dry',
    'punjab':        'hot_dry',
    # Heavy rainfall
    'assam':         'heavy_rainfall',
    'meghalaya':     'heavy_rainfall',
    'manipur':       'heavy_rainfall',
    'mizoram':       'heavy_rainfall',
    'nagaland':      'heavy_rainfall',
    'sikkim':        'heavy_rainfall',
    'arunachal':     'heavy_rainfall',
    'tripura':       'heavy_rainfall',
    'west bengal':   'heavy_rainfall',
    'bengal':        'heavy_rainfall',
    'odisha':        'cyclone_prone',
    'orissa':        'cyclone_prone',
    # Cyclone-prone
    'andhra':        'cyclone_prone',
    # Cold & hilly
    'himachal':      'cold_hilly',
    'uttarakhand':   'cold_hilly',
    'jammu':         'cold_hilly',
    'kashmir':       'cold_hilly',
    'ladakh':        'cold_hilly',
    'darjeeling':    'cold_hilly',
}


def _state_to_climate(state):
    """Return the Product climate field name for a given state string, or None."""
    if not state:
        return None
    state_lower = state.lower()
    for keyword, climate in _STATE_CLIMATE_MAP.items():
        if keyword in state_lower:
            return climate
    return None


def _get_recommendations(user, limit=8):
    """
    Return a list of Product objects personalised for this user.

    Logic (in priority order):
    1. Products matching user's climate zone (from user.state), excluding already viewed
    2. If < 4 climate matches found, top-rated active products excluding viewed
    """
    from apps.products.models import Product, ViewHistory

    viewed_ids = (
        ViewHistory.objects
        .filter(user=user)
        .values_list('product_id', flat=True)
    )

    qs = Product.objects.filter(is_active=True).exclude(id__in=viewed_ids)

    climate_field = _state_to_climate(getattr(user, 'state', '') or '')
    if climate_field:
        climate_qs = list(
            qs.filter(**{climate_field: True}).order_by('-total_reviews')[:limit]
        )
        if len(climate_qs) >= 4:
            return climate_qs

    # Fallback: top-rated products the user hasn't seen yet
    return list(qs.order_by('-total_reviews')[:limit])


# ══════════════════════════════════════════════════════════════════════════════
# RECOMMENDATIONS PAGE
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def recommendations_view(request):
    """
    Full recommendations page — personalised for the user's climate zone.

    URL: /recommendations/
    TEMPLATE: templates/users/recommendations.html
    """
    climate_field = _state_to_climate(getattr(request.user, 'state', '') or '')
    climate_label = {
        'coastal_humid':  'Coastal & Humid',
        'hot_dry':        'Hot & Dry',
        'heavy_rainfall': 'Heavy Rainfall',
        'cold_hilly':     'Cold & Hilly',
        'cyclone_prone':  'Cyclone-Prone Coast',
    }.get(climate_field, '')

    products = _get_recommendations(request.user, limit=24)

    return render(request, 'users/recommendations.html', {
        'products':      products,
        'climate_label': climate_label,
        'total_count':   len(products),
    })


# ══════════════════════════════════════════════════════════════════════════════
# VIEW HISTORY
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def view_history_view(request):
    """
    Full paginated view history for the logged-in user.

    URL: /history/
    TEMPLATE: templates/users/view_history.html
    """
    from apps.products.models import ViewHistory

    history = (
        ViewHistory.objects
        .filter(user=request.user)
        .select_related('product')
        .order_by('-viewed_at')
    )

    paginator = Paginator(history, 20)
    page_obj  = paginator.get_page(request.GET.get('page'))

    return render(request, 'users/view_history.html', {
        'page_obj':    page_obj,
        'total_count': paginator.count,
    })


# ══════════════════════════════════════════════════════════════════════════════
# PORTFOLIO VIEWS (Phase 2)
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def portfolio_upload_view(request):
    """
    Upload a new portfolio project image.

    SECURITY:
    - @login_required: must be authenticated
    - Only service providers should upload portfolio images (checked here)

    URL: /portfolio/add/
    """
    if not request.user.is_service_provider:
        messages.error(request, 'Only service providers can upload portfolio images.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = PortfolioImageForm(request.POST, request.FILES)
        if form.is_valid():
            portfolio_image = form.save(commit=False)
            portfolio_image.provider = request.user
            portfolio_image.save()
            messages.success(request, 'Project image added to your portfolio!')
            return redirect('dashboard')
    else:
        form = PortfolioImageForm()

    return render(request, 'users/portfolio_upload.html', {'form': form})


@login_required
def portfolio_delete_view(request, pk):
    """
    Delete a portfolio image. Only the owner can delete their own images.

    SECURITY:
    - @login_required: must be authenticated
    - We fetch with provider=request.user to ensure ownership

    URL: /portfolio/<pk>/delete/   (POST only)
    """
    image = get_object_or_404(PortfolioImage, pk=pk, provider=request.user)

    if request.method == 'POST':
        image.delete()
        messages.success(request, 'Portfolio image removed.')

    return redirect('dashboard')


# ══════════════════════════════════════════════════════════════════════════════
# DIRECTORY VIEWS (Phase 3)
# ══════════════════════════════════════════════════════════════════════════════

def _build_directory_queryset(user_type, request):
    """
    Shared helper: returns a filtered + sorted queryset of approved providers
    of a given user_type. Applies GET params: city, exp, spec, min_rating, sort.
    """
    type_filter = (
        {'user_type__in': user_type}
        if isinstance(user_type, (list, tuple))
        else {'user_type': user_type}
    )
    qs = (
        User.objects
        .filter(
            **type_filter,
            service_provider_profile__verification_status__in=['approved', 'pending'],
        )
        .select_related('service_provider_profile')
    )

    # ── Filters ────────────────────────────────────────────────────────────
    city = request.GET.get('city', '').strip()
    if city:
        qs = qs.filter(
            DQ(city__icontains=city) | DQ(district__icontains=city) | DQ(state__icontains=city)
        )

    exp = request.GET.get('exp', '')
    if exp == '0-5':
        qs = qs.filter(service_provider_profile__years_of_experience__lte=5)
    elif exp == '5-10':
        qs = qs.filter(
            service_provider_profile__years_of_experience__gt=5,
            service_provider_profile__years_of_experience__lte=10,
        )
    elif exp == '10-15':
        qs = qs.filter(
            service_provider_profile__years_of_experience__gt=10,
            service_provider_profile__years_of_experience__lte=15,
        )
    elif exp == '15+':
        qs = qs.filter(service_provider_profile__years_of_experience__gt=15)

    spec = request.GET.get('spec', '').strip()
    if spec:
        # JSON field — MySQL supports JSON_CONTAINS; use icontains as a fallback
        qs = qs.filter(service_provider_profile__specializations__icontains=spec)

    # ── Sort ────────────────────────────────────────────────────────────────
    sort = request.GET.get('sort', 'projects')
    if sort == 'experience':
        qs = qs.order_by('-service_provider_profile__years_of_experience')
    elif sort == 'recent':
        qs = qs.order_by('-service_provider_profile__created_at')
    else:  # default: most projects
        qs = qs.order_by('-service_provider_profile__total_projects_completed')

    return qs


@login_required
def contractor_directory_view(request):
    """
    Browse all verified contractors.

    URL: /contractors/
    TEMPLATE: templates/users/directory/list.html
    """
    qs = _build_directory_queryset('contractor', request)
    paginator = Paginator(qs, 12)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'users/directory/list.html', {
        'page_obj': page,
        'provider_type': 'contractor',
        'provider_type_label': 'Contractors',
        'active_city': request.GET.get('city', ''),
        'active_exp': request.GET.get('exp', ''),
        'active_spec': request.GET.get('spec', ''),
        'active_sort': request.GET.get('sort', 'projects'),
    })


@login_required
def architect_directory_view(request):
    """
    Browse all verified architects.

    URL: /architects/
    TEMPLATE: templates/users/directory/list.html
    """
    qs = _build_directory_queryset('architect', request)
    paginator = Paginator(qs, 12)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'users/directory/list.html', {
        'page_obj': page,
        'provider_type': 'architect',
        'provider_type_label': 'Architects',
        'active_city': request.GET.get('city', ''),
        'active_exp': request.GET.get('exp', ''),
        'active_spec': request.GET.get('spec', ''),
        'active_sort': request.GET.get('sort', 'projects'),
    })


@login_required
def designer_directory_view(request):
    """
    Browse all verified interior designers and architects.

    URL: /designers/
    TEMPLATE: templates/users/directory/list.html
    """
    qs = _build_directory_queryset(['interior_designer', 'architect'], request)
    paginator = Paginator(qs, 12)
    page = paginator.get_page(request.GET.get('page'))

    return render(request, 'users/directory/list.html', {
        'page_obj': page,
        'provider_type': 'interior_designer',  # keeps template URL logic → /designer/<username>/
        'provider_type_label': 'Designers & Architects',
        'active_city': request.GET.get('city', ''),
        'active_exp': request.GET.get('exp', ''),
        'active_spec': request.GET.get('spec', ''),
        'active_sort': request.GET.get('sort', 'projects'),
    })


# ══════════════════════════════════════════════════════════════════════════════
# RICH PUBLIC PROFILE + INQUIRY FORM (Phase 4)
# ══════════════════════════════════════════════════════════════════════════════

@login_required
def provider_profile_view(request, username):
    """
    Rich public profile for a verified service provider.
    Accessible at /contractor/<username>/, /architect/<username>/, /designer/<username>/

    SECURITY:
    - Only verified (approved) providers are shown to the public.
    - Admin users can see unverified profiles for review purposes.

    URL names: contractor_profile, architect_profile, designer_profile
    TEMPLATE: templates/users/provider_profile.html
    """
    provider_user = get_object_or_404(User, username=username)

    if not provider_user.is_service_provider:
        return redirect('home')

    try:
        profile = provider_user.service_provider_profile
    except ServiceProviderProfile.DoesNotExist:
        return redirect('home')

    # Non-admin users can only see approved providers
    if not profile.is_verified and not (request.user.is_authenticated and request.user.is_staff):
        messages.info(request, 'This profile is pending verification.')
        return redirect('home')

    # Portfolio images — featured items first, then newest first within each group
    all_portfolio = provider_user.portfolio_images.order_by('-featured', '-created_at')

    is_own_profile = request.user.is_authenticated and request.user == provider_user

    # Handle POST — either a banner/photo upload (own profile) or an inquiry
    inquiry_sent = False
    if request.method == 'POST':
        action = request.POST.get('_action', '')

        if action == 'upload_banner' and is_own_profile and 'banner_image' in request.FILES:
            profile.banner_image = request.FILES['banner_image']
            profile.save()
            return redirect(request.path)

        elif action == 'upload_photo' and is_own_profile and 'profile_photo' in request.FILES:
            provider_user.profile_photo = request.FILES['profile_photo']
            provider_user.save()
            return redirect(request.path)

        else:
            # Default: inquiry form
            sender_name = request.POST.get('sender_name', '').strip()
            sender_email = request.POST.get('sender_email', '').strip()
            sender_phone = request.POST.get('sender_phone', '').strip()
            message = request.POST.get('message', '').strip()

            if sender_name and sender_email and message:
                ServiceInquiry.objects.create(
                    provider=provider_user,
                    sender_name=sender_name,
                    sender_email=sender_email,
                    sender_phone=sender_phone,
                    message=message,
                )
                inquiry_sent = True
                messages.success(
                    request,
                    f'Your inquiry has been sent to {profile.business_name}. '
                    'They will contact you within 1–2 business days.',
                )
            else:
                messages.error(request, 'Please fill in all required fields.')

    return render(request, 'users/provider_profile.html', {
        'profile_user':     provider_user,
        'provider_profile': profile,
        'all_portfolio':    all_portfolio,
        'inquiry_sent':     inquiry_sent,
        'is_own_profile':   is_own_profile,
    })
