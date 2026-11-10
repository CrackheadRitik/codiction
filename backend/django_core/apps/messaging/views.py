"""
Codiction — Messaging Views

REST APIs for conversations and messages.
"""

from django.db.models import Q
from django.utils import timezone
from django.views.generic import TemplateView
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.views.generic import TemplateView
from apps.accounts.models import User
from apps.messaging.models import Conversation, ConversationParticipant, Message
from apps.messaging.serializers import (
    ConversationSerializer,
    MessageCreateSerializer,
    MessageSerializer,
)


class ConversationListView(generics.ListAPIView):
    """
    GET /api/messaging/conversations/

    List current user's conversations.
    """

    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Conversation.objects.filter(participants=self.request.user).prefetch_related(
            "participants", "messages"
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["request"] = self.request
        return context


class ConversationCreateView(APIView):
    """
    POST /api/messaging/conversations/

    Create or get existing DM conversation with another user.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user_id = request.data.get("user_id")

        if not user_id:
            return Response(
                {"error": "user_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            other_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        try:
            conversation, created = Conversation.get_or_create_direct(
                request.user, other_user
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                "conversation": ConversationSerializer(
                    conversation, context={"request": request}
                ).data,
                "created": created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class MessageListView(generics.ListAPIView):
    """
    GET /api/messaging/conversations/<id>/messages/

    Get all messages in a conversation (paginated).
    """

    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs["conversation_id"]

        # Verify user is participant
        if not ConversationParticipant.objects.filter(
            conversation_id=conversation_id, user=self.request.user
        ).exists():
            return Message.objects.none()

        return Message.objects.filter(conversation_id=conversation_id).select_related(
            "sender"
        )


class SendMessageView(APIView):
    """
    POST /api/messaging/conversations/<id>/messages/

    Send a message in a conversation.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        # Verify participant
        try:
            participant = ConversationParticipant.objects.get(
                conversation_id=conversation_id,
                user=request.user,
            )
        except ConversationParticipant.DoesNotExist:
            return Response(
                {"error": "Conversation not found or you're not a participant"},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = MessageCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        message = Message.objects.create(
            conversation_id=conversation_id,
            sender=request.user,
            **serializer.validated_data,
        )

        # Update conversation last_message_at
        conversation = participant.conversation
        conversation.last_message_at = timezone.now()
        conversation.save(update_fields=["last_message_at"])

        return Response(
            MessageSerializer(message).data,
            status=status.HTTP_201_CREATED,
        )


class MarkAsReadView(APIView):
    """
    POST /api/messaging/conversations/<id>/read/

    Mark all messages in a conversation as read.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, conversation_id):
        # Verify participant
        try:
            participant = ConversationParticipant.objects.get(
                conversation_id=conversation_id,
                user=request.user,
            )
        except ConversationParticipant.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Mark messages as read (not own messages)
        updated = (
            Message.objects
            .filter(conversation_id=conversation_id, is_read=False)
            .exclude(sender=request.user)
            .update(is_read=True)
        )

        # Update participant's last_read_at
        participant.last_read_at = timezone.now()
        participant.save(update_fields=["last_read_at"])

        return Response({"marked_read": updated})


class UnreadCountView(APIView):
    """
    GET /api/messaging/unread/

    Total unread messages across all conversations.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        count = Message.objects.filter(
            conversation__participants=request.user,
            is_read=False,
        ).exclude(sender=request.user).count()

        return Response({"unread_count": count})


class SearchUsersView(generics.ListAPIView):
    """
    GET /api/messaging/users/?q=<query>

    Search users to start a conversation.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()

        if len(query) < 2:
            return Response(
                {"error": "Search query must be at least 2 characters"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        users = (
            User.objects
            .filter(Q(email__icontains=query) | Q(first_name__icontains=query))
            .exclude(id=request.user.id)
            .order_by("email")[:20]
        )

        from apps.messaging.serializers import ParticipantSerializer

        return Response(
            ParticipantSerializer(users, many=True).data
        )
   


class MessagingListPageView(TemplateView):
    """Frontend: Conversations list page."""
    template_name = "messaging/list.html"


class ChatPageView(TemplateView):
    """Frontend: Chat window page."""
    template_name = "messaging/chat.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["conversation_id"] = str(kwargs.get("conversation_id"))
        return context