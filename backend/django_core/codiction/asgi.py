"""
ASGI config for Codiction.

Handles HTTP + WebSocket connections via Django Channels.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "codiction.settings.development")

# Initialize Django ASGI application early
django_asgi_app = get_asgi_application()

# Import routing AFTER Django setup
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402

from apps.messaging.routing import websocket_urlpatterns  # noqa: E402
from codiction.middleware import JWTAuthMiddlewareStack  # noqa: E402

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
        "websocket": JWTAuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
    }
)