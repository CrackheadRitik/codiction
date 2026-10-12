"""
Codiction — Accounts Admin

Django admin configuration for User model.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin panel configuration for User model."""

    list_display = ["email", "role", "xp", "streak", "is_active", "is_staff"]
    list_filter = ["role", "is_active", "is_staff", "email_verified", "totp_enabled"]
    search_fields = ["email", "first_name", "last_name"]
    ordering = ["-date_joined"]
    readonly_fields = ["id", "last_login", "date_joined"]

    fieldsets = (
        (None, {"fields": ("id", "email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "bio", "avatar_url")}),
        (_("Role & Gamification"), {"fields": ("role", "xp", "streak")}),
        (_("Security"), {"fields": ("totp_secret", "totp_enabled", "email_verified")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "role"),
        }),
    )
