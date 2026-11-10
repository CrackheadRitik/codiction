"""
Codiction — Accounts Frontend URLs
"""

from django.urls import path

from apps.accounts.views import (
    IndexView,
    LoginPageView,
    ProfilePageView,
    RegisterPageView,
)

app_name = "accounts_frontend"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", LoginPageView.as_view(), name="login-page"),
    path("register/", RegisterPageView.as_view(), name="register-page"),
    path("profile/", ProfilePageView.as_view(), name="profile"),
]