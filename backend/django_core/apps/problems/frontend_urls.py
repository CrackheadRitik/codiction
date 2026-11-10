"""
Codiction — Problems Frontend URLs

Page routes for problems (HTML pages, not API).
"""

from django.urls import path

from apps.problems.views import (
    ProblemDetailPageView,
    ProblemListPageView,
)

app_name = "problems_frontend"

urlpatterns = [
    path("problems/", ProblemListPageView.as_view(), name="list"),
    path("problems/<slug:slug>/", ProblemDetailPageView.as_view(), name="detail"),
]