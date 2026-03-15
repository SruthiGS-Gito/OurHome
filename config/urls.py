"""
config/urls.py — The MAIN URL router for the entire OurHome project.

HOW THIS FILE WORKS:
- This is the FIRST file Django checks when a request comes in (ROOT_URLCONF in settings.py).
- Django goes through urlpatterns from TOP to BOTTOM, trying to match the URL.
- When it finds a match, it calls the corresponding view.
- include() delegates a URL prefix to another app's urls.py file.

URL ROUTING ORDER MATTERS:
- 'admin/' → Django admin panel
- 'accounts/' → allauth handles login, signup, email verify, password reset
- '' (empty) → our users app URLs (dashboard, profile, search, etc.)
- '' (empty) → home page (catches everything else at root /)
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from apps.products.views import home_view

urlpatterns = [
    # Django admin panel — accessible at /admin/
    path('admin/', admin.site.urls),

    # Static / placeholder pages
    path('about/', TemplateView.as_view(template_name='pages/about.html'), name='about'),
    path('privacy/', TemplateView.as_view(template_name='pages/privacy.html'), name='privacy'),
    path('terms/', TemplateView.as_view(template_name='pages/terms.html'), name='terms'),

    # allauth URLs — handles ALL authentication:
    # /accounts/login/         → Login page
    # /accounts/signup/        → Customer signup (uses our CustomerSignupForm)
    # /accounts/logout/        → Logout
    # /accounts/confirm-email/ → Email verification
    # /accounts/password/reset/→ Forgot password
    # /accounts/password/change/ → Change password (when logged in)
    path('accounts/', include('allauth.urls')),

    # Our users app URLs — dashboard, profile, search, provider signup
    path('', include('apps.users.urls')),

    # Products app URLs — /materials/ catalog and /materials/<slug>/ detail
    path('', include('apps.products.urls')),

    # Home page — passes featured_products + climate_cards to template
    path('', home_view, name='home'),
]

# Serve uploaded media files during development
# In production, these are served by nginx/Apache (not Django)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
