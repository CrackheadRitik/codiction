"""
Codiction — Companies Admin
"""

from django.contrib import admin

from apps.companies.models import Company, ProblemCompany


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "logo_url", "website", "created_at"]
    search_fields = ["name"]
    prepopulated_fields = {}  # No slug field


@admin.register(ProblemCompany)
class ProblemCompanyAdmin(admin.ModelAdmin):
    list_display = ["problem", "company", "frequency", "last_asked"]
    list_filter = ["company"]
    search_fields = ["problem__title", "company__name"]
    autocomplete_fields = ["problem", "company"]