"""
Codiction — Submissions URLs
"""

from django.urls import path

from apps.submissions.views import (
    SubmissionDetailView,
    SubmissionListView,
    SubmissionStatusView,
    SubmitCodeView,
)

app_name = "submissions"

urlpatterns = [
    path("submit/", SubmitCodeView.as_view(), name="submit"),
    path("", SubmissionListView.as_view(), name="list"),
    path("<uuid:id>/", SubmissionDetailView.as_view(), name="detail"),
    path("<uuid:id>/status/", SubmissionStatusView.as_view(), name="status"),
]