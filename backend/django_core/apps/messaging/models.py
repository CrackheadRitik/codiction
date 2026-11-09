"""
Codiction — Messaging Models

Conversations and messages for in-app DMs.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Conversation(BaseModel):
    """
    A conversation (1:1 DM for MVP, can extend to group later).
    """

    class Type(models.TextChoices):
        DIRECT = "direct", _("Direct Message")
        GROUP = "group", _("Group Chat")  # Future

    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.DIRECT,
        db_index=True,
    )
    participants = models.ManyToManyField(
        "accounts.User",
        through="ConversationParticipant",
        related_name="conversations",
    )
    last_message_at = models.DateTimeField(blank=True, null=True, db_index=True)

    class Meta:
        db_table = "conversations"
        ordering = ["-last_message_at", "-created_at"]
        indexes = [
            models.Index(fields=["-last_message_at"]),
        ]

    def __str__(self) -> str:
        return f"Conversation {self.id} ({self.type})"

    @classmethod
    def get_or_create_direct(cls, user1, user2):
        """Get or create a 1:1 conversation between two users."""
        from django.db.models import Count, Q

        if user1.id == user2.id:
            raise ValueError("Cannot create conversation with yourself")

        # Find existing conversation with exactly these 2 users
        existing = (
            cls.objects
            .filter(type=cls.Type.DIRECT)
            .annotate(participant_count=Count("participants"))
            .filter(participant_count=2)
            .filter(participants=user1)
            .filter(participants=user2)
            .first()
        )

        if existing:
            return existing, False

        # Create new conversation
        conversation = cls.objects.create(type=cls.Type.DIRECT)
        ConversationParticipant.objects.create(conversation=conversation, user=user1)
        ConversationParticipant.objects.create(conversation=conversation, user=user2)
        return conversation, True


class ConversationParticipant(models.Model):
    """Users in a conversation."""

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="participant_links",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="conversation_links",
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    last_read_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = "conversation_participants"
        unique_together = ("conversation", "user")
        indexes = [
            models.Index(fields=["user"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} in {self.conversation_id}"


class Message(BaseModel):
    """A message in a conversation."""

    class MessageType(models.TextChoices):
        TEXT = "text", _("Text")
        CODE = "code", _("Code Snippet")
        SYSTEM = "system", _("System Message")

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="sent_messages",
    )
    content = models.TextField(max_length=2000)
    message_type = models.CharField(
        max_length=20,
        choices=MessageType.choices,
        default=MessageType.TEXT,
    )
    is_read = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["conversation", "is_read"]),
        ]

    def __str__(self) -> str:
        return f"{self.sender.email}: {self.content[:50]}"