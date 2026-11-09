"""
Codiction — Leaderboard Admin
"""

from django.contrib import admin

from apps.leaderboard.models import Badge, LeaderboardCache, UserBadge


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ["name", "description", "created_at"]
    search_fields = ["name"]


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ["user", "badge", "earned_at"]
    list_filter = ["badge", "earned_at"]
    search_fields = ["user__email", "badge__name"]


@admin.register(LeaderboardCache)
class LeaderboardCacheAdmin(admin.ModelAdmin):
    list_display = ["scope", "company_name", "period", "updated_at"]
    list_filter = ["scope"]