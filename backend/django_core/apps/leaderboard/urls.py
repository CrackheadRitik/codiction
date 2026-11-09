"""
Codiction — Leaderboard URLs
"""

from django.urls import path

from apps.leaderboard.views import (
    CompanyLeaderboardView,
    GlobalLeaderboardView,
    MyRankView,
)

app_name = "leaderboard"

urlpatterns = [
    path("global/", GlobalLeaderboardView.as_view(), name="global"),
    path("me/", MyRankView.as_view(), name="me"),
    path("company/<str:company_name>/", CompanyLeaderboardView.as_view(), name="company"),
]