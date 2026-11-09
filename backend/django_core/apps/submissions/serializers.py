"""
Codiction — Submissions Serializers

DRF serializers for Submission model.
"""

from rest_framework import serializers

from apps.submissions.models import Submission


class SubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new submission."""

    class Meta:
        model = Submission
        fields = ["problem", "code", "language", "is_sample_run"]

    def validate_language(self, value):
        """Validate language is supported."""
        if value not in dict(Submission.Language.choices):
            raise serializers.ValidationError(f"Unsupported language: {value}")
        return value

    def validate_code(self, value):
        """Validate code length."""
        if len(value) > 50000:
            raise serializers.ValidationError("Code exceeds 50,000 character limit.")
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Code is too short.")
        return value

    def create(self, validated_data):
        """Create submission tied to current user."""
        validated_data["user"] = self.context["request"].user
        validated_data["verdict"] = Submission.Verdict.PENDING
        return super().create(validated_data)


class SubmissionListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for submission list."""

    problem_title = serializers.CharField(source="problem.title", read_only=True)
    problem_slug = serializers.CharField(source="problem.slug", read_only=True)
    verdict_display = serializers.CharField(source="get_verdict_display", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "problem_title",
            "problem_slug",
            "language",
            "verdict",
            "verdict_display",
            "runtime_ms",
            "memory_mb",
            "is_sample_run",
            "created_at",
        ]


class SubmissionDetailSerializer(serializers.ModelSerializer):
    """Full serializer for submission detail."""

    problem_title = serializers.CharField(source="problem.title", read_only=True)
    problem_slug = serializers.CharField(source="problem.slug", read_only=True)
    verdict_display = serializers.CharField(source="get_verdict_display", read_only=True)
    language_display = serializers.CharField(source="get_language_display", read_only=True)

    class Meta:
        model = Submission
        fields = [
            "id",
            "problem_title",
            "problem_slug",
            "code",
            "language",
            "language_display",
            "verdict",
            "verdict_display",
            "runtime_ms",
            "memory_mb",
            "error_message",
            "is_sample_run",
            "created_at",
        ]