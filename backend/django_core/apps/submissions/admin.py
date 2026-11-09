"""
Codiction — Submissions Admin

Admin configuration for Submission model.
"""

from django.contrib import admin
from django.utils.html import format_html

from apps.submissions.models import Submission


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    """Admin panel for Submission model."""

    list_display = [
        "short_id",
        "user_email",
        "problem_title",
        "language",
        "verdict_badge",
        "runtime_ms",
        "is_sample_run",
        "created_at",
    ]
    list_filter = ["verdict", "language", "is_sample_run", "created_at"]
    search_fields = ["user__email", "problem__title", "judge0_token"]
    readonly_fields = [
        "id",
        "user",
        "problem",
        "code",
        "language",
        "verdict",
        "runtime_ms",
        "memory_mb",
        "error_message",
        "judge0_token",
        "is_sample_run",
        "created_at",
        "updated_at",
    ]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    def has_add_permission(self, request):
        return False  # Submissions are created only via API

    def has_change_permission(self, request, obj=None):
        return False  # Read-only view

    def short_id(self, obj):
        return str(obj.id)[:8]

    short_id.short_description = "ID"

    def user_email(self, obj):
        return obj.user.email

    user_email.short_description = "User"
    user_email.admin_order_field = "user__email"

    def problem_title(self, obj):
        return obj.problem.title

    problem_title.short_description = "Problem"
    problem_title.admin_order_field = "problem__title"

    def verdict_badge(self, obj):
        """Colored badge for verdict."""
        colors = {
            "AC": "#10b981",
            "WA": "#ef4444",
            "TLE": "#f59e0b",
            "MLE": "#f59e0b",
            "RE": "#dc2626",
            "CE": "#6b7280",
            "SE": "#7c3aed",
            "PENDING": "#3b82f6",
        }
        color = colors.get(obj.verdict, "#6b7280")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.get_verdict_display(),
        )

    verdict_badge.short_description = "Verdict"
    verdict_badge.admin_order_field = "verdict"