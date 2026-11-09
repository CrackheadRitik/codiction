"""
Codiction — WebSocket Authentication Middleware

Custom middleware to authenticate WebSocket connections via JWT token.
"""

import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

logger = logging.getLogger(__name__)


@database_sync_to_async
def get_user_from_token(token):
    """Decode JWT and return the user."""
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    from rest_framework_simplejwt.tokens import AccessToken

    User = get_user_model()

    try:
        access_token = AccessToken(token)
        user_id = access_token["user_id"]
        user = User.objects.get(id=user_id)
        logger.info(f"✅ JWT auth success for user {user.email}")
        return user
    except InvalidToken as e:
        logger.warning(f"❌ InvalidToken: {e}")
        return AnonymousUser()
    except TokenError as e:
        logger.warning(f"❌ TokenError: {e}")
        return AnonymousUser()
    except User.DoesNotExist:
        logger.warning(f"❌ User does not exist for user_id from token")
        return AnonymousUser()
    except KeyError as e:
        logger.warning(f"❌ KeyError: {e}")
        return AnonymousUser()
    except Exception as e:
        logger.error(f"❌ Unexpected: {type(e).__name__}: {e}")
        return AnonymousUser()


class JWTAuthMiddleware(BaseMiddleware):
    """Custom middleware that authenticates WebSocket connections via JWT."""

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode()
        query_params = parse_qs(query_string)

        token = query_params.get("token", [None])[0]

        logger.info(f"🔍 WS handshake: query_string_length={len(query_string)}, token_present={bool(token)}")

        if token:
            scope["user"] = await get_user_from_token(token)
            logger.info(f"🔍 After auth: user={scope['user']}, is_auth={scope['user'].is_authenticated if hasattr(scope['user'], 'is_authenticated') else 'N/A'}")
        else:
            scope["user"] = AnonymousUser()
            logger.warning("❌ No token in query string")

        return await super().__call__(scope, receive, send)


def JWTAuthMiddlewareStack(inner):
    """Wrap the middleware stack."""
    return JWTAuthMiddleware(inner)