"""
apps/users/admin.py — Django Admin configuration for User and ServiceProviderProfile.

WHAT IS DJANGO ADMIN?
- Django comes with a built-in admin panel at /admin/
- It lets you view, create, edit, and delete database records through a web interface
- You "register" your models here to make them appear in the admin panel

WHY UserAdmin INSTEAD OF ModelAdmin?
- Django's default ModelAdmin would show the password as a raw text field.
- UserAdmin provides: password hashing, user creation forms with password confirmation,
  permission management, and group assignment.
- If we used ModelAdmin, admins could accidentally set invalid passwords.

ADMIN ACTIONS:
- Custom actions let you perform bulk operations on selected rows.
- We add "Approve" and "Reject" actions for service provider verification.
- Select multiple providers → Action dropdown → "Approve selected" → Click Go.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from .models import User, ServiceProviderProfile, PortfolioImage, ServiceInquiry


# ── Inline: must be defined BEFORE the admin class that uses it ──────────────

class PortfolioImageInline(admin.TabularInline):
    """Inline editor for portfolio images — attached to CustomUserAdmin (FK provider→User)."""
    model = PortfolioImage
    fk_name = 'provider'
    extra = 0
    fields = ('image', 'project_title', 'project_type', 'featured', 'completion_date')
    show_change_link = True


# ── User admin ───────────────────────────────────────────────────────────────

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Admin interface for the User model.

    @admin.register(User) is a DECORATOR — it tells Django:
    "Use this class as the admin interface for the User model."
    Same as writing: admin.site.register(User, CustomUserAdmin)
    """

    inlines = [PortfolioImageInline]

    # list_display: which columns appear in the user list table
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active', 'date_joined')

    # list_filter: filter sidebar on the right side of the list
    list_filter = ('user_type', 'is_active', 'is_staff', 'state', 'district')

    # search_fields: which fields are searched when you type in the search box
    search_fields = ('email', 'first_name', 'last_name', 'phone')

    # ordering: default sort order (- means descending, so newest first)
    ordering = ('-date_joined',)

    # fieldsets: how the edit form is organized into sections
    # We ADD our custom sections to UserAdmin's existing fieldsets
    fieldsets = UserAdmin.fieldsets + (
        ('OurHome Profile', {
            'fields': ('phone', 'user_type', 'profile_photo', 'bio', 'date_of_birth'),
        }),
        ('Location', {
            'fields': ('city', 'district', 'state', 'pincode'),
        }),
    )

    # add_fieldsets: fields shown when CREATING a new user in admin
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('OurHome Info', {
            'fields': ('email', 'phone', 'user_type'),
        }),
    )


# ── Service provider profile admin ───────────────────────────────────────────

@admin.register(ServiceProviderProfile)
class ServiceProviderProfileAdmin(admin.ModelAdmin):
    """
    Admin interface for ServiceProviderProfile.
    This is where admins verify/approve/reject service providers.
    """

    # Columns in the list view
    list_display = (
        'business_name', 'user', 'get_user_type',
        'verification_status', 'years_of_experience', 'created_at',
    )

    # Filter sidebar
    list_filter = ('verification_status', 'user__user_type')

    # Search
    search_fields = ('business_name', 'user__email', 'user__first_name')

    # Fields that can't be edited (timestamps are auto-set; verified_by is set by actions)
    readonly_fields = ('created_at', 'updated_at', 'verified_by')

    # Custom admin actions (shown in the action dropdown above the list)
    actions = ['approve_providers', 'reject_providers', 'mark_under_review']

    def get_user_type(self, obj):
        """
        Custom column: shows "Contractor" instead of "contractor".
        get_user_type_display() is a Django method auto-generated for Choice fields.
        It converts the stored value to the human-readable label.
        """
        return obj.user.get_user_type_display()
    get_user_type.short_description = 'Provider Type'

    @admin.action(description='Approve selected providers')
    def approve_providers(self, request, queryset):
        """
        Bulk approve selected providers.
        queryset = the selected rows in the admin list.
        .update() runs a single SQL UPDATE query (efficient for bulk operations).
        Also records which admin performed the approval.
        """
        updated = queryset.update(
            verification_status='approved',
            verified_at=timezone.now(),
            verified_by=request.user,
        )
        self.message_user(request, f'{updated} provider(s) approved.')

    @admin.action(description='Reject selected providers')
    def reject_providers(self, request, queryset):
        """Bulk reject selected providers."""
        updated = queryset.update(
            verification_status='rejected',
            verified_by=request.user,
        )
        self.message_user(request, f'{updated} provider(s) rejected.')

    @admin.action(description='Mark selected providers as Under Review')
    def mark_under_review(self, request, queryset):
        """Move providers to 'under_review' status while being evaluated."""
        updated = queryset.update(verification_status='under_review')
        self.message_user(request, f'{updated} provider(s) marked as Under Review.')


# ── Portfolio image admin ─────────────────────────────────────────────────────

@admin.register(PortfolioImage)
class PortfolioImageAdmin(admin.ModelAdmin):
    list_display = ('project_title', 'provider', 'project_type', 'featured', 'completion_date', 'created_at')
    list_filter = ('project_type', 'featured')
    search_fields = ('project_title', 'provider__email', 'project_location')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


# ── Service inquiry admin ─────────────────────────────────────────────────────

@admin.register(ServiceInquiry)
class ServiceInquiryAdmin(admin.ModelAdmin):
    list_display = ('sender_name', 'sender_email', 'provider', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('sender_name', 'sender_email', 'provider__email')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
