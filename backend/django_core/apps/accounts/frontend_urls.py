"""
Codiction — Accounts Frontend URLs

Page routes for auth pages.
"""

from django.urls import path

from apps.accounts.views import IndexView, LoginPageView, RegisterPageView

app_name = "accounts_frontend"

urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("login/", LoginPageView.as_view(), name="login-page"),
    path("register/", RegisterPageView.as_view(), name="register-page"),
]