"""
Codiction — Messaging Serializers
"""

from rest_framework import serializers

from apps.accounts.models import User
from apps.messaging.models import Conversation, Message


class ParticipantSerializer(serializers.ModelSerializer):
    """Minimal user info for conversation participants."""

    username = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "avatar_url"]

    def get_username(self, obj):
        return obj.email.split("@")[0]


class MessageSerializer(serializers.ModelSerializer):
    """Serializer for a message."""

    sender_username = serializers.SerializerMethodField()
    sender_avatar = serializers.CharField(source="sender.avatar_url", read_only=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "conversation",
            "sender",
            "sender_username",
            "sender_avatar",
            "content",
            "message_type",
            "is_read",
            "created_at",
        ]
        read_only_fields = ["id", "sender", "created_at"]

    def get_sender_username(self, obj):
        return obj.sender.email.split("@")[0]


class ConversationSerializer(serializers.ModelSerializer):
    """Serializer for conversation list."""

    participants = ParticipantSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "type",
            "participants",
            "last_message",
            "unread_count",
            "last_message_at",
            "created_at",
        ]

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by("-created_at").first()
        if last_msg:
            return {
                "content": last_msg.content[:100],
                "sender": last_msg.sender.email.split("@")[0],
                "created_at": last_msg.created_at,
            }
        return None

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return 0
        return obj.messages.filter(is_read=False).exclude(sender=request.user).count()


class MessageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating messages."""

    class Meta:
        model = Message
        fields = ["content", "message_type"]

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Message content cannot be empty.")
        if len(value) > 2000:
            raise serializers.ValidationError("Message exceeds 2000 character limit.")
        return value.strip()