"""
Codiction — User Model

Custom user model with:
- UUID primary key
- Email-based login (no username)
- Profile fields (avatar, bio)
- Gamification fields (xp, streak)
- 2FA fields (totp_secret)
"""

import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.accounts.managers import UserManager


class User(AbstractUser):
    """
    Custom user model for Codiction.

    Replaces default Django User with:
    - UUID primary key
    - Email as login field
    - Additional profile/gamification fields
    """

    class Role(models.TextChoices):
        """User role choices."""

        USER = "user", _("User")
        MODERATOR = "moderator", _("Moderator")
        ADMIN = "admin", _("Admin")

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier (UUID v4)",
    )

    username = None

    email = models.EmailField(
        _("email address"),
        unique=True,
        db_index=True,
        help_text="Used for login and notifications",
    )

    avatar_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to user's avatar image",
    )

    bio = models.TextField(
        blank=True,
        null=True,
        max_length=500,
        help_text="Short bio (max 500 chars)",
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        db_index=True,
        help_text="User's role (user, moderator, admin)",
    )

    xp = models.IntegerField(
        default=0,
        help_text="Experience points earned",
    )

    streak = models.IntegerField(
        default=0,
        help_text="Consecutive days of coding",
    )

    totp_secret = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        help_text="TOTP secret for 2FA",
    )

    totp_enabled = models.BooleanField(
        default=False,
        help_text="Whether 2FA is enabled",
    )

    email_verified = models.BooleanField(
        default=False,
        help_text="Whether email is verified",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = _("User")
        verbose_name_plural = _("Users")

    def __str__(self) -> str:
        return self.email
