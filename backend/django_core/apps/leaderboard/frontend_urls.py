from django.urls import path
from apps.leaderboard.views import LeaderboardPageView

app_name = "leaderboard_frontend"

urlpatterns = [
    path("leaderboard/", LeaderboardPageView.as_view(), name="global"),
]