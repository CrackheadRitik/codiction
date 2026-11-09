"""
Codiction — Messaging WebSocket Consumers

Real-time chat via Django Channels.
"""

import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.messaging.models import Conversation, ConversationParticipant, Message

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time chat in a conversation.

    URL: ws://localhost:8000/ws/messaging/<conversation_id>/

    Events:
        Client → Server:
            - {"type": "message.send", "content": "...", "message_type": "text"}
            - {"type": "typing.start"}
            - {"type": "typing.stop"}
            - {"type": "message.read", "message_id": "..."}

        Server → Client:
            - {"type": "connection.established", "conversation_id": "...", ...}
            - {"type": "message.new", "message": {...}}
            - {"type": "user.typing", "user_id": "...", "username": "...", "is_typing": true}
            - {"type": "message.read", "message_id": "...", "read_by": "..."}
            - {"type": "error", "message": "..."}
    """

    async def connect(self):
        """
        Called when a WebSocket connection is attempted.
        - Authenticates the user
        - Verifies user is a participant in the conversation
        - Joins the conversation's channel group
        """
        self.user = self.scope.get("user")
        self.conversation_id = self.scope["url_route"]["kwargs"]["conversation_id"]
        self.room_group_name = f"chat_{self.conversation_id}"

        # Reject if not authenticated
        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Reject if user is not a participant
        is_participant = await self.verify_participant()
        if not is_participant:
            await self.close(code=4003)
            return

        # Join the conversation group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name,
        )

        await self.accept()

        # Send connection confirmation
        await self.send(text_data=json.dumps({
            "type": "connection.established",
            "conversation_id": str(self.conversation_id),
            "user": {
                "id": str(self.user.id),
                "username": self.user.email.split("@")[0],
            },
        }))

    async def disconnect(self, close_code):
        """Called when WebSocket disconnects."""
        if hasattr(self, "room_group_name"):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name,
            )

    async def receive(self, text_data):
        """
        Called when a message is received from the WebSocket client.
        """
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_error("Invalid JSON")
            return

        event_type = data.get("type")

        if event_type == "message.send":
            await self.handle_send_message(data)
        elif event_type == "typing.start":
            await self.handle_typing(data, True)
        elif event_type == "typing.stop":
            await self.handle_typing(data, False)
        elif event_type == "message.read":
            await self.handle_mark_read(data)
        else:
            await self.send_error(f"Unknown event type: {event_type}")

    # =====================================================
    # EVENT HANDLERS
    # =====================================================
    async def handle_send_message(self, data):
        """Handle incoming message from client."""
        content = data.get("content", "").strip()
        message_type = data.get("message_type", "text")

        if not content:
            await self.send_error("Content cannot be empty")
            return

        if len(content) > 2000:
            await self.send_error("Message too long (max 2000 chars)")
            return

        # Save message to DB
        message = await self.create_message(content, message_type)

        if not message:
            await self.send_error("Failed to save message")
            return

        # Broadcast to all participants in the conversation
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_message",
                "message": {
                    "id": str(message["id"]),
                    "content": message["content"],
                    "message_type": message["message_type"],
                    "sender": {
                        "id": str(message["sender_id"]),
                        "username": message["sender_username"],
                        "avatar_url": message["sender_avatar"],
                    },
                    "created_at": message["created_at"],
                    "is_read": False,
                },
            },
        )

    async def handle_typing(self, data, is_typing):
        """Broadcast typing indicator."""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "broadcast_typing",
                "user_id": str(self.user.id),
                "username": self.user.email.split("@")[0],
                "is_typing": is_typing,
            },
        )

    async def handle_mark_read(self, data):
        """Mark a message as read."""
        message_id = data.get("message_id")
        if not message_id:
            await self.send_error("message_id is required")
            return

        success = await self.mark_message_read(message_id)
        if success:
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "broadcast_read",
                    "message_id": message_id,
                    "read_by": str(self.user.id),
                },
            )

    # =====================================================
    # GROUP EVENT HANDLERS (called when group sends)
    # =====================================================
    async def broadcast_message(self, event):
        """Send a new message to the WebSocket client."""
        await self.send(text_data=json.dumps({
            "type": "message.new",
            "message": event["message"],
        }))

    async def broadcast_typing(self, event):
        """Send typing indicator to the WebSocket client."""
        # Don't echo back to the sender
        if event["user_id"] == str(self.user.id):
            return

        await self.send(text_data=json.dumps({
            "type": "user.typing",
            "user_id": event["user_id"],
            "username": event["username"],
            "is_typing": event["is_typing"],
        }))

    async def broadcast_read(self, event):
        """Send read receipt to the WebSocket client."""
        await self.send(text_data=json.dumps({
            "type": "message.read",
            "message_id": event["message_id"],
            "read_by": event["read_by"],
        }))

    async def send_error(self, message):
        """Send error message to client."""
        await self.send(text_data=json.dumps({
            "type": "error",
            "message": message,
        }))

    # =====================================================
    # DATABASE HELPERS (sync → async)
    # =====================================================
    @database_sync_to_async
    def verify_participant(self):
        """Check if user is a participant in this conversation."""
        return ConversationParticipant.objects.filter(
            conversation_id=self.conversation_id,
            user=self.user,
        ).exists()

    @database_sync_to_async
    def create_message(self, content, message_type):
        """Create a message in the database."""
        try:
            message = Message.objects.create(
                conversation_id=self.conversation_id,
                sender=self.user,
                content=content,
                message_type=message_type,
            )

            # Update conversation last_message_at
            Conversation.objects.filter(id=self.conversation_id).update(
                last_message_at=timezone.now()
            )

            return {
                "id": message.id,
                "content": message.content,
                "message_type": message.message_type,
                "sender_id": message.sender.id,
                "sender_username": message.sender.email.split("@")[0],
                "sender_avatar": message.sender.avatar_url,
                "created_at": message.created_at.isoformat(),
            }
        except Exception as e:
            print(f"Error creating message: {e}")
            return None

    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark a message as read."""
        try:
            updated = Message.objects.filter(
                id=message_id,
                conversation_id=self.conversation_id,
            ).exclude(sender=self.user).update(is_read=True)
            return updated > 0
        except Exception:
            return False