"""
apps/users/adapters.py — Custom adapter for django-allauth.

WHAT IS AN ADAPTER?
- allauth uses the "adapter pattern" to let you customize its behavior
  WITHOUT modifying allauth's source code.
- Think of it as a "hook" — allauth calls methods on the adapter at key moments
  (saving a user, redirecting after login, etc.) and you override those methods
  to inject your custom logic.

WHY DO WE NEED THIS?
- allauth doesn't know about our custom fields (phone, user_type, etc.)
- allauth uses username for accounts, but we want email-only login.
- We need to auto-generate usernames from emails.
- We want to redirect service providers to 'complete profile' after login.

CONFIGURED IN settings.py:
    ACCOUNT_ADAPTER = 'apps.users.adapters.AccountAdapter'
"""

from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    """
    Customizes how allauth creates users and handles redirects.

    DefaultAccountAdapter is allauth's base class with default behavior.
    We override specific methods to customize:
    1. save_user — how a new user is created during signup
    2. get_login_redirect_url — where to go after login
    """

    def save_user(self, request, user, form, commit=True):
        """
        Called by allauth when creating a new user from the signup form.

        HOW THIS METHOD IS CALLED:
        1. User fills out signup form and clicks "Create Account"
        2. allauth validates the form (email unique? password strong enough?)
        3. allauth creates a User object with email and password
        4. allauth calls THIS METHOD to let us set additional fields
        5. We set phone, user_type, first_name, last_name from the form data
        6. The user is saved to the database

        PARAMETERS:
        - request: the HTTP request object (contains session, cookies, etc.)
        - user: the User object (already has email and password set)
        - form: our CustomerSignupForm or ServiceProviderSignupForm
        - commit: if True, save to database now. If False, just set fields (save later).
        """
        # Call the parent's save_user first — it sets email and password
        user = super().save_user(request, user, form, commit=False)

        # Auto-generate a username from the email prefix
        # e.g., "john@gmail.com" → username "john"
        # We need this because Django's User model requires a username field,
        # even though WE login with email. allauth also uses it internally.
        email_prefix = user.email.split('@')[0]
        user.username = self._generate_unique_username(email_prefix)

        # Set our custom fields from the form data
        # form.cleaned_data is a dictionary of validated form values
        # .get('field', '') returns '' if the field doesn't exist (safe fallback)
        user.phone = form.cleaned_data.get('phone', '')
        user.user_type = form.cleaned_data.get('user_type', 'customer')
        user.first_name = form.cleaned_data.get('first_name', '')
        user.last_name = form.cleaned_data.get('last_name', '')

        if commit:
            user.save()
        return user

    def _generate_unique_username(self, base):
        """
        Generates a unique username from an email prefix.

        WHY THIS IS NEEDED:
        If two users sign up as john@gmail.com and john@yahoo.com,
        both would get username "john". This method adds a number
        suffix: "john", "john1", "john2", etc.

        HOW IT WORKS:
        1. Start with the base (e.g., "john")
        2. Check if that username already exists in the database
        3. If yes, try "john1", "john2", etc. until we find one that's free
        """
        from apps.users.models import User

        username = base
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base}{counter}"
            counter += 1
        return username

    def get_login_redirect_url(self, request):
        """
        Called by allauth after a successful login.
        Returns the URL to redirect to.

        OUR LOGIC:
        - If the user is a service provider and hasn't completed their profile,
          redirect them to the profile completion page.
        - Otherwise, redirect to the dashboard.

        WHY THIS MATTERS:
        A contractor who signed up but never filled in their business details
        should be reminded to complete their profile before doing anything else.
        """
        user = request.user
        if user.is_service_provider and not user.is_profile_complete:
            return '/profile/complete/'
        return '/dashboard/'
