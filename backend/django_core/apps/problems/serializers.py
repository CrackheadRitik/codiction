"""
Codiction — Problems Serializers

DRF serializers for Problem, Topic, and TestCase models.
"""

from rest_framework import serializers

from apps.problems.models import (
    Problem,
    ProblemTopic,
    TestCase,
    Topic,
)


# =====================================================
# TOPIC
# =====================================================
class TopicSerializer(serializers.ModelSerializer):
    """Serializer for Topic model."""

    problem_count = serializers.IntegerField(source="problems.count", read_only=True)

    class Meta:
        model = Topic
        fields = ["id", "name", "slug", "description", "problem_count"]


class TopicListSerializer(serializers.ModelSerializer):
    """Lightweight topic serializer (for dropdowns, filters)."""

    class Meta:
        model = Topic
        fields = ["id", "name", "slug"]


# =====================================================
# TEST CASE
# =====================================================
class TestCaseSerializer(serializers.ModelSerializer):
    """Serializer for TestCase model."""

    class Meta:
        model = TestCase
        fields = ["id", "input_data", "expected_output", "is_sample", "is_hidden", "order"]


class TestCasePublicSerializer(serializers.ModelSerializer):
    """Public test case serializer — hides hidden test cases."""

    class Meta:
        model = TestCase
        fields = ["id", "input_data", "expected_output", "order"]


# =====================================================
# PROBLEM
# =====================================================
class ProblemListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for problem list view."""

    topics = TopicListSerializer(many=True, read_only=True)
    difficulty_display = serializers.CharField(source="get_difficulty_display", read_only=True)

    class Meta:
        model = Problem
        fields = [
            "id",
            "title",
            "slug",
            "difficulty",
            "difficulty_display",
            "acceptance_rate",
            "topics",
            "is_premium",
            "created_at",
        ]


class ProblemDetailSerializer(serializers.ModelSerializer):
    """Full serializer for problem detail view."""

    topics = TopicListSerializer(many=True, read_only=True)
    sample_test_cases = serializers.SerializerMethodField()
    difficulty_display = serializers.CharField(source="get_difficulty_display", read_only=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)

    class Meta:
        model = Problem
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "difficulty",
            "difficulty_display",
            "acceptance_rate",
            "examples",
            "constraints",
            "hints",
            "topics",
            "sample_test_cases",
            "source",
            "source_display",
            "is_premium",
            "created_at",
            "updated_at",
        ]

    def get_sample_test_cases(self, obj):
        """Return only sample test cases (not hidden ones)."""
        sample_cases = obj.test_cases.filter(is_sample=True)
        return TestCasePublicSerializer(sample_cases, many=True).data


class ProblemCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating problems (admin only)."""

    topic_ids = serializers.PrimaryKeyRelatedField(
        queryset=Topic.objects.all(),
        many=True,
        write_only=True,
        required=False,
    )

    class Meta:
        model = Problem
        fields = [
            "id",
            "title",
            "slug",
            "description",
            "difficulty",
            "acceptance_rate",
            "examples",
            "constraints",
            "hints",
            "solution_python",
            "solution_java",
            "solution_cpp",
            "solution_javascript",
            "source",
            "is_published",
            "is_premium",
            "topic_ids",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        """Create problem and assign topics."""
        topic_ids = validated_data.pop("topic_ids", [])
        problem = Problem.objects.create(**validated_data)
        for topic in topic_ids:
            ProblemTopic.objects.create(problem=problem, topic=topic)
        return problem

    def update(self, instance, validated_data):
        """Update problem and reassign topics."""
        topic_ids = validated_data.pop("topic_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if topic_ids is not None:
            ProblemTopic.objects.filter(problem=instance).delete()
            for topic in topic_ids:
                ProblemTopic.objects.create(problem=instance, topic=topic)

        return instance