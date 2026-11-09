"""
Codiction — Companies Models

Company tags for problems.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import BaseModel


class Company(BaseModel):
    """Tech company (Google, Amazon, Meta, etc.)."""

    name = models.CharField(max_length=50, unique=True, db_index=True)
    logo_url = models.URLField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    class Meta:
        db_table = "companies"
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ProblemCompany(models.Model):
    """Junction: Problem ↔ Company."""

    problem = models.ForeignKey(
        "problems.Problem",
        on_delete=models.CASCADE,
        related_name="companies",
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="problems")
    frequency = models.IntegerField(default=0)
    last_asked = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "problem_companies"
        unique_together = ("problem", "company")
        indexes = [
            models.Index(fields=["problem"]),
            models.Index(fields=["company"]),
        ]

    def __str__(self) -> str:
        return f"{self.problem.title} → {self.company.name}"