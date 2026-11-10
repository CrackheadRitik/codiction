"""
Codiction — Root URL configuration.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def health_check(request):
    """Health check endpoint."""
    return JsonResponse({"status": "ok", "service": "codiction-api"})


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health_check, name="health-check"),
    path("api/accounts/", include("apps.accounts.urls", namespace="accounts")),
    path("api/", include("apps.problems.urls", namespace="problems")),
    path("api/submissions/", include("apps.submissions.urls", namespace="submissions")),
    path("api/leaderboard/", include("apps.leaderboard.urls", namespace="leaderboard")),
    path("api/messaging/", include("apps.messaging.urls", namespace="messaging")),

    path("", include("apps.accounts.frontend_urls", namespace="accounts_frontend")),
    path("", include("apps.problems.frontend_urls", namespace="problems_frontend")),
    path("", include("apps.leaderboard.frontend_urls", namespace="leaderboard_frontend")),
    path("", include("apps.messaging.frontend_urls", namespace="messaging_frontend")),

    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)