from django.contrib import admin

from .models import Candidate, Company, JobApplication, JobPosting


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "website")
    search_fields = ("name", "location")
    ordering = ("name",)


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company",
        "job_type",
        "location",
        "application_deadline",
        "is_active",
        "posted_date",
    )
    list_filter = ("job_type", "is_active", "location")
    search_fields = ("title", "company__name", "location", "required_skills")
    ordering = ("-posted_date",)
    list_editable = ("is_active",)
    autocomplete_fields = ("company",)
    date_hierarchy = "posted_date"


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone")
    search_fields = ("full_name", "email", "phone")
    ordering = ("full_name",)


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("candidate", "job", "status", "resume", "applied_at")
    list_filter = ("status", "job")
    search_fields = ("candidate__full_name", "candidate__email", "job__title")
    ordering = ("-applied_at",)
    list_select_related = ("candidate", "job", "job__company")
    autocomplete_fields = ("job", "candidate")
