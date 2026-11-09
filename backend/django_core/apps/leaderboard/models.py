"""
Codiction — Leaderboard Models

Badges and leaderboard cache.
"""

import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Badge(BaseModel):
    """Achievement badge."""

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon_url = models.URLField(blank=True, null=True)
    criteria = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "badges"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class UserBadge(BaseModel):
    """Badge earned by user."""

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="badges",
    )
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_badges"
        unique_together = ("user", "badge")
        ordering = ["-earned_at"]

    def __str__(self) -> str:
        return f"{self.user.email} → {self.badge.name}"


class LeaderboardCache(BaseModel):
    """Cached leaderboard data (updated periodically by Celery)."""

    class Scope(models.TextChoices):
        GLOBAL = "global", _("Global")
        COMPANY = "company", _("Company")
        WEEKLY = "weekly", _("Weekly")
        MONTHLY = "monthly", _("Monthly")

    scope = models.CharField(max_length=20, choices=Scope.choices, db_index=True)
    company_name = models.CharField(max_length=50, blank=True, null=True)
    period = models.CharField(max_length=20, blank=True, null=True)
    rankings = models.JSONField(default=list)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "leaderboard_cache"
        indexes = [
            models.Index(fields=["scope", "company_name"]),
        ]

    def __str__(self) -> str:
        return f"{self.scope} - {self.company_name or 'All'}"