"""
Codiction — Core Models

Abstract base models shared across all apps.
Every model in Codiction inherits from BaseModel for consistency.
"""

import uuid

from django.db import models as basemodels


class BaseModel(basemodels.Model):
    """
    Abstract base model with UUID primary key and timestamps.

    All Codiction models should inherit from this class to get:
    - UUID primary key (secure, non-guessable)
    - created_at timestamp (auto-set on creation)
    - updated_at timestamp (auto-updated on save)
    """

    id = basemodels.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier (UUID v4)",
    )
    created_at = basemodels.DateTimeField(
        auto_now_add=True,
        help_text="When this record was created",
    )
    updated_at = basemodels.DateTimeField(
        auto_now=True,
        help_text="When this record was last updated",
    )

    class Meta:
        abstract = True  # No database table for this model
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return str(self.id)
