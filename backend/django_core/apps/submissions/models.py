"""
Codiction — Submissions Models

Defines the Submission model for tracking code submissions.
"""

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Submission(BaseModel):
    """
    A user's code submission for a problem.

    Tracks:
    - User, problem, code, language
    - Verdict (AC, WA, TLE, RE, CE, PENDING)
    - Runtime and memory usage
    - Judge0 token for async tracking
    """

    class Verdict(models.TextChoices):
        PENDING = "PENDING", _("Pending")
        AC = "AC", _("Accepted")
        WA = "WA", _("Wrong Answer")
        TLE = "TLE", _("Time Limit Exceeded")
        MLE = "MLE", _("Memory Limit Exceeded")
        RE = "RE", _("Runtime Error")
        CE = "CE", _("Compilation Error")
        SE = "SE", _("System Error")

    class Language(models.TextChoices):
        PYTHON = "python", _("Python 3.11")
        JAVA = "java", _("Java 17")
        CPP = "cpp", _("C++ 20")
        JAVASCRIPT = "javascript", _("JavaScript (Node 20)")
        GO = "go", _("Go 1.21")

    # =====================================================
    # RELATIONSHIPS
    # =====================================================
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="submissions",
        help_text="User who made the submission",
    )
    problem = models.ForeignKey(
        "problems.Problem",
        on_delete=models.CASCADE,
        related_name="submissions",
        help_text="Problem being solved",
    )

    # =====================================================
    # CODE
    # =====================================================
    code = models.TextField(
        help_text="The source code submitted",
    )
    language = models.CharField(
        max_length=20,
        choices=Language.choices,
        help_text="Programming language used",
    )

    # =====================================================
    # RESULT
    # =====================================================
    verdict = models.CharField(
        max_length=10,
        choices=Verdict.choices,
        default=Verdict.PENDING,
        db_index=True,
        help_text="Result of judging",
    )
    runtime_ms = models.IntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Execution time in milliseconds",
    )
    memory_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Memory usage in megabytes",
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error details (compile error, runtime error, etc.)",
    )

    # =====================================================
    # JUDGE0 TRACKING
    # =====================================================
    judge0_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        help_text="Judge0 submission token for async tracking",
    )

    # =====================================================
    # METADATA
    # =====================================================
    is_sample_run = models.BooleanField(
        default=False,
        help_text="True if this was a 'Run' (sample tests only), not 'Submit'",
    )

    class Meta:
        db_table = "submissions"
        verbose_name = _("Submission")
        verbose_name_plural = _("Submissions")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["problem", "verdict"]),
            models.Index(fields=["verdict"]),
            models.Index(fields=["judge0_token"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.email} - {self.problem.title} - {self.verdict}"

    @property
    def is_accepted(self) -> bool:
        """True if verdict is AC."""
        return self.verdict == self.Verdict.AC

    @property
    def is_pending(self) -> bool:
        """True if verdict is PENDING."""
        return self.verdict == self.Verdict.PENDING