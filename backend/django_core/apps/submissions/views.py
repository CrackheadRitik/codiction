"""
Codiction — Submissions Views

API endpoints for code submission and history.
"""

from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.problems.models import Problem
from apps.submissions.models import Submission
from apps.submissions.serializers import (
    SubmissionCreateSerializer,
    SubmissionDetailSerializer,
    SubmissionListSerializer,
)
from apps.submissions.tasks import judge_submission


class SubmitCodeView(APIView):
    """
    POST /api/submissions/submit/

    Submit code for judging. Creates submission + queues async judge.
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = SubmissionCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        submission = serializer.save()

        # Queue async judging via Celery
        judge_submission.delay(str(submission.id))

        return Response(
            {
                "id": str(submission.id),
                "verdict": submission.verdict,
                "message": "Submission queued for judging.",
            },
            status=status.HTTP_201_CREATED,
        )


class SubmissionListView(generics.ListAPIView):
    """
    GET /api/submissions/

    List current user's submissions (most recent first).
    """

    serializer_class = SubmissionListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Submission.objects.filter(user=self.request.user).select_related("problem")

        # Filter by problem slug
        problem_slug = self.request.query_params.get("problem")
        if problem_slug:
            queryset = queryset.filter(problem__slug=problem_slug)

        return queryset


class SubmissionDetailView(generics.RetrieveAPIView):
    """
    GET /api/submissions/<id>/

    Retrieve a single submission (only owner can view).
    """

    serializer_class = SubmissionDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "id"

    def get_queryset(self):
        return Submission.objects.filter(user=self.request.user).select_related("problem")


class SubmissionStatusView(APIView):
    """
    GET /api/submissions/<id>/status/

    Lightweight polling endpoint for submission status.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        submission = get_object_or_404(
            Submission, id=id, user=request.user
        )
        return Response(
            {
                "id": str(submission.id),
                "verdict": submission.verdict,
                "runtime_ms": submission.runtime_ms,
                "memory_mb": str(submission.memory_mb) if submission.memory_mb else None,
                "error_message": submission.error_message,
            }
        )