"""
Codiction — Problems Views

API endpoints for problems and topics.
"""

from django.db.models import Count, Q
from django.views.generic import TemplateView
from rest_framework import filters, generics, permissions
from rest_framework.pagination import PageNumberPagination

from apps.problems.models import Problem, Topic
from apps.problems.serializers import (
    ProblemDetailSerializer,
    ProblemListSerializer,
    TopicListSerializer,
    TopicSerializer,
)


class ProblemPagination(PageNumberPagination):
    """Custom pagination for problem list."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class ProblemListView(generics.ListAPIView):
    """
    GET /api/problems/

    List all published problems with filtering, search, and pagination.

    Query params:
        - difficulty: Easy | Medium | Hard
        - topic: topic slug (e.g., "arrays")
        - search: keyword (searches title + description)
        - page: page number
        - page_size: results per page (max 100)

    Examples:
        /api/problems/?difficulty=Easy
        /api/problems/?topic=arrays
        /api/problems/?search=two+sum
        /api/problems/?difficulty=Medium&topic=dynamic-programming
    """

    serializer_class = ProblemListSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = ProblemPagination

    def get_queryset(self):
        """Filter and annotate the queryset."""
        queryset = (
            Problem.objects.filter(is_published=True)
            .prefetch_related("topics")
            .order_by("-created_at")
        )

        # Filter by difficulty
        difficulty = self.request.query_params.get("difficulty")
        if difficulty:
            queryset = queryset.filter(difficulty__iexact=difficulty)

        # Filter by topic slug
        topic_slug = self.request.query_params.get("topic")
        if topic_slug:
            queryset = queryset.filter(topics__slug=topic_slug)

        # Search by title or description
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        return queryset.distinct()


class ProblemDetailView(generics.RetrieveAPIView):
    """
    GET /api/problems/<slug>/

    Retrieve a single problem with full details, sample test cases, and topics.
    """

    queryset = (
        Problem.objects.filter(is_published=True)
        .prefetch_related("topics", "test_cases")
    )
    serializer_class = ProblemDetailSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"


class TopicListView(generics.ListAPIView):
    """
    GET /api/topics/

    List all topics with problem counts.
    """

    queryset = Topic.objects.annotate(problem_count=Count("problems")).order_by("name")
    serializer_class = TopicSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None


class TopicDetailView(generics.RetrieveAPIView):
    """
    GET /api/topics/<slug>/

    Retrieve a single topic with its problems.
    """

    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"

class ProblemListPageView(TemplateView):
    template_name = "problems/list.html"


class ProblemListPageView(TemplateView):
    """Frontend: Problem list page."""
    template_name = "problems/list.html"


class ProblemDetailPageView(TemplateView):
    """Frontend: Problem detail page with Monaco editor."""
    template_name = "problems/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["slug"] = kwargs.get("slug")
        return context