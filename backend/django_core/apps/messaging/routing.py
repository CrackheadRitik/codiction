"""
Codiction — Messaging WebSocket Routing
"""

from django.urls import re_path

from apps.messaging.consumers import ChatConsumer

websocket_urlpatterns = [
    re_path(
        r"^ws/messaging/(?P<conversation_id>[0-9a-f-]+)/$",
        ChatConsumer.as_asgi(),
    ),
]