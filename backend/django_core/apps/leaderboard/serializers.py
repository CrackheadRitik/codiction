"""
Codiction — Leaderboard Serializers
"""

from rest_framework import serializers


class LeaderboardEntrySerializer(serializers.Serializer):
    """A single entry in the leaderboard."""

    rank = serializers.IntegerField()
    user_id = serializers.UUIDField()
    username = serializers.CharField()
    avatar_url = serializers.URLField(allow_null=True)
    xp = serializers.IntegerField()
    streak = serializers.IntegerField()
    solved_count = serializers.IntegerField()


class UserRankSerializer(serializers.Serializer):
    """Current user's rank."""

    rank = serializers.IntegerField()
    total_users = serializers.IntegerField()
    solved_count = serializers.IntegerField()
    xp = serializers.IntegerField()