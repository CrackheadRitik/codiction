"""
Codiction — Problems Models

Defines the Problem, Topic, and TestCase models.
"""

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Topic(BaseModel):
    """
    Topic tag (e.g., Arrays, Dynamic Programming, Trees).

    Used for filtering problems and tracking user weaknesses.
    """

    name = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="Topic name (e.g., 'Dynamic Programming')",
    )
    slug = models.SlugField(
        max_length=60,
        unique=True,
        db_index=True,
        help_text="URL-friendly version (e.g., 'dynamic-programming')",
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Brief description of the topic",
    )

    class Meta:
        db_table = "topics"
        verbose_name = _("Topic")
        verbose_name_plural = _("Topics")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Problem(BaseModel):
    """
    A coding problem.

    Contains description, difficulty, solutions in multiple languages,
    and relationships to topics and companies.
    """

    class Difficulty(models.TextChoices):
        EASY = "Easy", _("Easy")
        MEDIUM = "Medium", _("Medium")
        HARD = "Hard", _("Hard")

    class Source(models.TextChoices):
        AI_GENERATED = "AI_Generated", _("AI Generated")
        OPEN_SOURCE = "OpenSource", _("Open Source")
        CROWDSOURCED = "Crowdsourced", _("Crowdsourced")
        EXPERT = "Expert", _("Expert Curated")

    # =====================================================
    # BASIC INFO
    # =====================================================
    title = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Problem title",
    )
    slug = models.SlugField(
        max_length=300,
        unique=True,
        db_index=True,
        help_text="URL-friendly version of title",
    )
    description = models.TextField(
        help_text="Full problem description (Markdown supported)",
    )

    # =====================================================
    # DIFFICULTY & METADATA
    # =====================================================
    difficulty = models.CharField(
        max_length=10,
        choices=Difficulty.choices,
        db_index=True,
        help_text="Problem difficulty level",
    )
    acceptance_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Percentage of users who solved it (0-100)",
    )

    # =====================================================
    # EXAMPLES (shown to user)
    # =====================================================
    examples = models.JSONField(
        default=list,
        blank=True,
        help_text="List of {'input': ..., 'output': ..., 'explanation': ...}",
    )
    constraints = models.JSONField(
        default=list,
        blank=True,
        help_text="List of constraint strings",
    )
    hints = models.JSONField(
        default=list,
        blank=True,
        help_text="List of hint strings (progressively revealed)",
    )

    # =====================================================
    # SOLUTIONS (for reference / post-solve)
    # =====================================================
    solution_python = models.TextField(blank=True, null=True)
    solution_java = models.TextField(blank=True, null=True)
    solution_cpp = models.TextField(blank=True, null=True)
    solution_javascript = models.TextField(blank=True, null=True)

    # =====================================================
    # METADATA
    # =====================================================
    source = models.CharField(
        max_length=50,
        choices=Source.choices,
        default=Source.AI_GENERATED,
        help_text="Where this problem came from",
    )
    is_published = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether visible to users",
    )
    is_premium = models.BooleanField(
        default=False,
        help_text="Whether requires Pro subscription",
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================
    topics = models.ManyToManyField(
        Topic,
        through="ProblemTopic",
        related_name="problems",
        help_text="Topics this problem belongs to",
    )

    class Meta:
        db_table = "problems"
        verbose_name = _("Problem")
        verbose_name_plural = _("Problems")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["difficulty"]),
            models.Index(fields=["is_published"]),
            models.Index(fields=["-created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.difficulty})"

    def save(self, *args, **kwargs):
        """Auto-generate slug from title if not provided."""
        if not self.slug:
            self.slug = slugify(self.title)[:300]
        super().save(*args, **kwargs)


class ProblemTopic(models.Model):
    """
    Many-to-many junction for Problem ↔ Topic.

    Explicit through table gives us room to add fields later
    (e.g., relevance_score, is_primary).
    """

    problem = models.ForeignKey(Problem, on_delete=models.CASCADE)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "problem_topics"
        verbose_name = _("Problem Topic")
        verbose_name_plural = _("Problem Topics")
        unique_together = ("problem", "topic")
        indexes = [
            models.Index(fields=["problem"]),
            models.Index(fields=["topic"]),
        ]

    def __str__(self) -> str:
        return f"{self.problem.title} → {self.topic.name}"


class TestCase(models.Model):
    """
    Test case for a problem.

    Each problem has multiple test cases (both sample and hidden).
    - Sample: shown to user in problem description
    - Hidden: used for judging submissions
    """

    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        related_name="test_cases",
    )
    input_data = models.TextField(
        help_text="Input passed to user's code (as string)",
    )
    expected_output = models.TextField(
        help_text="Expected output from user's code",
    )
    is_sample = models.BooleanField(
        default=False,
        help_text="If True, shown to users in problem description",
    )
    is_hidden = models.BooleanField(
        default=False,
        help_text="If True, used for judging submissions",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Ordering for display / execution",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "test_cases"
        verbose_name = _("Test Case")
        verbose_name_plural = _("Test Cases")
        ordering = ["order", "created_at"]
        indexes = [
            models.Index(fields=["problem", "is_sample"]),
            models.Index(fields=["problem", "is_hidden"]),
        ]

    def __str__(self) -> str:
        type_ = "Sample" if self.is_sample else "Hidden"
        return f"{self.problem.title} — {type_} #{self.order}"