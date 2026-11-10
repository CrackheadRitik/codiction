"""
Codiction — Leaderboard Views

APIs for global and company-specific leaderboards.
"""

from django.db.models import Count, Q
from django.views.generic import TemplateView
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import User
from apps.leaderboard.serializers import (
    LeaderboardEntrySerializer,
    UserRankSerializer,
)
from apps.submissions.models import Submission


class GlobalLeaderboardView(APIView):
    """
    GET /api/leaderboard/global/

    Returns top 100 users by solved problems, then by XP.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Aggregate AC submissions per user
        users = (
            User.objects
            .annotate(
                solved_count=Count(
                    "submissions",
                    filter=Q(submissions__verdict="AC", submissions__is_sample_run=False),
                    distinct=True,
                )
            )
            .filter(solved_count__gt=0)
            .order_by("-solved_count", "-xp", "-streak")[:100]
        )

        rankings = [
            {
                "rank": idx + 1,
                "user_id": str(user.id),
                "username": user.email.split("@")[0],
                "avatar_url": user.avatar_url,
                "xp": user.xp,
                "streak": user.streak,
                "solved_count": user.solved_count,
            }
            for idx, user in enumerate(users)
        ]

        return Response({
            "scope": "global",
            "count": len(rankings),
            "rankings": LeaderboardEntrySerializer(rankings, many=True).data,
        })


class MyRankView(APIView):
    """
    GET /api/leaderboard/me/

    Returns current user's rank + stats.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # Count my solved problems
        my_solved = Submission.objects.filter(
            user=user, verdict="AC", is_sample_run=False
        ).values("problem").distinct().count()

        # Count users with more solved problems
        users_above = (
            User.objects
            .annotate(
                solved_count=Count(
                    "submissions",
                    filter=Q(submissions__verdict="AC", submissions__is_sample_run=False),
                    distinct=True,
                )
            )
            .filter(solved_count__gt=my_solved)
            .count()
        )

        # Total ranked users
        total_users = (
            User.objects
            .annotate(
                solved_count=Count(
                    "submissions",
                    filter=Q(submissions__verdict="AC", submissions__is_sample_run=False),
                    distinct=True,
                )
            )
            .filter(solved_count__gt=0)
            .count()
        )

        return Response({
            "rank": users_above + 1,
            "total_users": total_users,
            "solved_count": my_solved,
            "xp": user.xp,
        })

class CompanyLeaderboardView(APIView):
    """
    GET /api/leaderboard/company/<company_name>/

    Top users for a specific company.
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request, company_name):
        try:
            from apps.companies.models import ProblemCompany

            problem_ids = ProblemCompany.objects.filter(
                company__name__iexact=company_name
            ).values_list("problem_id", flat=True)

            if not problem_ids:
                return Response(
                    {
                        "scope": "company",
                        "company": company_name,
                        "count": 0,
                        "rankings": [],
                        "message": f"No problems found for company: {company_name}",
                    }
                )

            users = (
                User.objects
                .annotate(
                    solved_count=Count(
                        "submissions",
                        filter=Q(
                            submissions__verdict="AC",
                            submissions__is_sample_run=False,
                            submissions__problem_id__in=problem_ids,
                        ),
                        distinct=True,
                    )
                )
                .filter(solved_count__gt=0)
                .order_by("-solved_count", "-xp")[:50]
            )

            rankings = [
                {
                    "rank": idx + 1,
                    "user_id": str(user.id),
                    "username": user.email.split("@")[0],
                    "avatar_url": user.avatar_url,
                    "xp": user.xp,
                    "streak": user.streak,
                    "solved_count": user.solved_count,
                }
                for idx, user in enumerate(users)
            ]

            return Response({
                "scope": "company",
                "company": company_name,
                "count": len(rankings),
                "rankings": LeaderboardEntrySerializer(rankings, many=True).data,
            })

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class LeaderboardPageView(TemplateView):
    """Frontend: Leaderboard page."""
    template_name = "leaderboard/global.html"

class ProfilePageView(TemplateView):
    """Frontend: User profile page."""
    template_name = "profile/me.html"