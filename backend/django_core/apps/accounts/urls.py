"""
Codiction — Accounts URLs

URL routes for authentication endpoints.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import (
    LoginView,
    LogoutView,
    MeView,
    RegisterView,
    UserDetailView,
)

app_name = "accounts"

urlpatterns = [
    # Authentication
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("refresh/", TokenRefreshView.as_view(), name="token-refresh"),

    # User profile
    path("me/", MeView.as_view(), name="me"),
    path("users/<uuid:id>/", UserDetailView.as_view(), name="user-detail"),
]