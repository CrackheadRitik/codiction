"""
Codiction — Problems URLs

URL routes for problems and topics.
"""

from django.urls import path

from apps.problems.views import (
    ProblemDetailView,
    ProblemListView,
    TopicDetailView,
    TopicListView,
)

app_name = "problems"

urlpatterns = [
    # Problems
    path("problems/", ProblemListView.as_view(), name="problem-list"),
    path("problems/<slug:slug>/", ProblemDetailView.as_view(), name="problem-detail"),

    # Topics
    path("topics/", TopicListView.as_view(), name="topic-list"),
    path("topics/<slug:slug>/", TopicDetailView.as_view(), name="topic-detail"),
]