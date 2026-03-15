"""
apps/users/urls.py — URL patterns for the users app.

HOW DJANGO URL ROUTING WORKS:
1. User visits a URL (e.g., /dashboard/)
2. Django starts at config/urls.py (ROOT_URLCONF)
3. config/urls.py has: path('', include('apps.users.urls'))
   This means: "for any URL, also check apps/users/urls.py"
4. Django finds path('dashboard/', views.dashboard_view, name='dashboard')
5. Django calls dashboard_view(request)

THE name= PARAMETER:
- Gives the URL a NAME so you can reference it in templates and code
  WITHOUT hardcoding the URL path.
- In templates: {% url 'dashboard' %} → /dashboard/
- In Python: redirect('dashboard') → redirect to /dashboard/
- WHY? If you later change the URL from /dashboard/ to /home/,
  you only change it HERE — every template and view automatically updates.

<int:user_id> IN URL PATTERNS:
- <int:user_id> is a URL parameter. It captures a number from the URL.
- Example: /provider/42/ → user_id=42 is passed to the view function.
- int: means it must be a whole number (not text).
"""

from django.urls import path
from . import views

urlpatterns = [
    # Dashboard — main page after login
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Profile — view and edit your own profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),

    # Profile completion — for service providers who need to fill in business info
    path('profile/complete/', views.profile_complete_view, name='profile_complete'),

    # Service provider signup — separate registration flow
    path('provider/signup/', views.service_provider_signup_view, name='provider_signup'),

    # Legacy public profile by user ID (kept for backward compat)
    path('provider/<int:user_id>/', views.public_profile_view, name='public_profile'),

    # Portfolio — upload and delete project images (provider dashboard)
    path('portfolio/add/', views.portfolio_upload_view, name='portfolio_add'),
    path('portfolio/<int:pk>/delete/', views.portfolio_delete_view, name='portfolio_delete'),

    # Directory pages — browse verified providers by type
    path('contractors/', views.contractor_directory_view, name='contractor_directory'),
    path('architects/', views.architect_directory_view, name='architect_directory'),
    path('designers/', views.designer_directory_view, name='designer_directory'),

    # Rich public profiles — accessible by username, under type-specific URLs
    path('contractor/<str:username>/', views.provider_profile_view, name='contractor_profile'),
    path('architect/<str:username>/', views.provider_profile_view, name='architect_profile'),
    path('designer/<str:username>/', views.provider_profile_view, name='designer_profile'),

    # Recommendations — personalised product suggestions
    path('recommendations/', views.recommendations_view, name='recommendations'),

    # View history — full list of all products the user has viewed
    path('history/', views.view_history_view, name='view_history'),

    # Search — search across materials, contractors, architects, designers
    path('search/', views.search_view, name='search'),
]
