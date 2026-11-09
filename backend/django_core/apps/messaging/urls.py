"""
Codiction — Messaging URLs
"""

from django.urls import path

from apps.messaging.views import (
    ConversationCreateView,
    ConversationListView,
    MarkAsReadView,
    MessageListView,
    SearchUsersView,
    SendMessageView,
    UnreadCountView,
)

app_name = "messaging"

urlpatterns = [
    # Conversations
    path("conversations/", ConversationListView.as_view(), name="conversation-list"),
    path("conversations/create/", ConversationCreateView.as_view(), name="conversation-create"),

    # Messages
    path(
        "conversations/<uuid:conversation_id>/messages/",
        MessageListView.as_view(),
        name="message-list",
    ),
    path(
        "conversations/<uuid:conversation_id>/messages/send/",
        SendMessageView.as_view(),
        name="message-send",
    ),
    path(
        "conversations/<uuid:conversation_id>/read/",
        MarkAsReadView.as_view(),
        name="mark-read",
    ),

    # Utility
    path("unread/", UnreadCountView.as_view(), name="unread-count"),
    path("users/", SearchUsersView.as_view(), name="user-search"),
]