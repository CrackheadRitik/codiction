"""
Codiction — Problems Admin

Django admin configuration for Problem, Topic, and TestCase models.
"""

from django.contrib import admin
from django.utils.html import format_html

from apps.problems.models import (
    Problem,
    ProblemTopic,
    TestCase,
    Topic,
)


# =====================================================
# TOPIC
# =====================================================
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    """Admin panel for Topic model."""

    list_display = ["name", "slug", "problem_count", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["name", "description"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["id", "created_at", "updated_at"]
    ordering = ["name"]

    fieldsets = (
        (None, {"fields": ("id", "name", "slug", "description")}),
        ("Metadata", {"fields": ("created_at", "updated_at")}),
    )

    def problem_count(self, obj):
        """Count of problems with this topic."""
        return obj.problems.count()

    problem_count.short_description = "Problems"


# =====================================================
# INLINES
# =====================================================
class TestCaseInline(admin.TabularInline):
    """Inline test case editor inside Problem admin."""

    model = TestCase
    extra = 1
    fields = ["order", "input_data", "expected_output", "is_sample", "is_hidden"]
    ordering = ["order"]


class ProblemTopicInline(admin.TabularInline):
    """Inline topic assignment inside Problem admin."""

    model = ProblemTopic
    extra = 1
    fields = ["topic"]
    autocomplete_fields = ["topic"]


# =====================================================
# PROBLEM
# =====================================================
@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    """Admin panel for Problem model."""

    list_display = [
        "title",
        "difficulty_badge",
        "acceptance_rate",
        "topic_count",
        "is_published",
        "created_at",
    ]
    list_filter = ["difficulty", "is_published", "is_premium", "source", "created_at"]
    search_fields = ["title", "slug", "description"]
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ["id", "created_at", "updated_at", "topic_display"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"

    fieldsets = (
        ("Basic Info", {
            "fields": ("id", "title", "slug", "description", "difficulty", "acceptance_rate")
        }),
        ("Examples & Constraints", {
            "fields": ("examples", "constraints", "hints"),
            "classes": ("wide",),
        }),
        ("Solutions", {
            "fields": ("solution_python", "solution_java", "solution_cpp", "solution_javascript"),
            "classes": ("collapse",),
        }),
        ("Metadata", {
            "fields": ("source", "is_published", "is_premium")
        }),
        ("Topics", {
            "fields": ("topic_display",),
            "description": "Manage topics via the inline section below.",
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    inlines = [ProblemTopicInline, TestCaseInline]

    def difficulty_badge(self, obj):
        """Colored badge for difficulty."""
        colors = {
            "Easy": "#10b981",
            "Medium": "#f59e0b",
            "Hard": "#ef4444",
        }
        color = colors.get(obj.difficulty, "#6b7280")
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; '
            'border-radius: 4px; font-weight: bold;">{}</span>',
            color,
            obj.difficulty,
        )

    difficulty_badge.short_description = "Difficulty"
    difficulty_badge.admin_order_field = "difficulty"

    def topic_count(self, obj):
        """Number of topics."""
        return obj.topics.count()

    topic_count.short_description = "Topics"

    def topic_display(self, obj):
        """Display topics as comma-separated list."""
        topics = obj.topics.all()
        if not topics:
            return "No topics assigned"
        return ", ".join([t.name for t in topics])

    topic_display.short_description = "Assigned Topics"


# =====================================================
# TEST CASE (standalone)
# =====================================================
@admin.register(TestCase)
class TestCaseAdmin(admin.ModelAdmin):
    """Standalone TestCase admin (for direct management)."""

    list_display = ["problem", "order", "case_type", "created_at"]
    list_filter = ["is_sample", "is_hidden", "created_at"]
    search_fields = ["problem__title"]
    ordering = ["problem", "order"]
    autocomplete_fields = ["problem"]

    def case_type(self, obj):
        """Show test case type."""
        if obj.is_sample:
            return "📖 Sample"
        if obj.is_hidden:
            return "🔒 Hidden"
        return "❓ Unknown"

    case_type.short_description = "Type"