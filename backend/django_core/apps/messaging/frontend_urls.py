"""
Codiction — Messaging Frontend URLs
"""

from django.urls import path

from apps.messaging.views import ChatPageView, MessagingListPageView

app_name = "messaging_frontend"

urlpatterns = [
    path("messages/", MessagingListPageView.as_view(), name="list"),
    path("messages/<uuid:conversation_id>/", ChatPageView.as_view(), name="chat"),
]