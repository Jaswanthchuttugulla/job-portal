from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify
from django.utils.timezone import now


class Company(models.Model):
    """A company that posts job openings."""

    name = models.CharField(max_length=200)
    website = models.URLField(blank=True)
    location = models.CharField(max_length=200)
    logo_url = models.URLField(blank=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        ordering = ["name"]

    def __str__(self):
        return self.name


class JobPosting(models.Model):
    """A single job opening posted by a company."""

    class JobType(models.TextChoices):
        FULL_TIME = "FULL_TIME", "Full-Time"
        PART_TIME = "PART_TIME", "Part-Time"
        REMOTE = "REMOTE", "Remote Work"
        INTERNSHIP = "INTERNSHIP", "Internship"

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="job_postings"
    )
    title = models.CharField(max_length=200)
    job_type = models.CharField(
        max_length=20, choices=JobType.choices, default=JobType.FULL_TIME
    )
    location = models.CharField(max_length=200)
    required_skills = models.CharField(
        max_length=500,
        help_text="Comma-separated list of skills, e.g. 'Python, Django, SQL'",
    )
    salary_range = models.CharField(max_length=100, blank=True)
    description = models.TextField()
    application_deadline = models.DateField()
    is_active = models.BooleanField(default=True)
    posted_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-posted_date"]

    def __str__(self):
        return f"{self.title} at {self.company.name}"

    def skills_list(self):
        """Return required_skills as a clean list of individual skills."""
        return [skill.strip() for skill in self.required_skills.split(",") if skill.strip()]


class Candidate(models.Model):
    """A job seeker who has applied to at least one job posting."""

    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30)
    portfolio_url = models.URLField(blank=True)
    skills = models.CharField(max_length=500, blank=True)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    def skills_list(self):
        return [skill.strip() for skill in self.skills.split(",") if skill.strip()]


def resume_upload_path(instance, filename):
    """Store resumes under resumes/<year>/<month>/<candidate-name>_<timestamp>.<ext>"""
    ext = filename.split(".")[-1].lower()
    safe_name = slugify(instance.candidate.full_name) or "candidate"
    timestamp = now().strftime("%Y%m%d%H%M%S")
    return f"resumes/{now():%Y/%m}/{safe_name}_{timestamp}.{ext}"


class JobApplication(models.Model):
    """An application submitted by a candidate for a specific job posting."""

    class Status(models.TextChoices):
        APPLIED = "APPLIED", "Application Received"
        REVIEW = "REVIEW", "Under HR Review"
        SHORTLIST = "SHORTLIST", "Shortlisted for Interview"
        REJECTED = "REJECTED", "Not Selected"

    job = models.ForeignKey(
        JobPosting, on_delete=models.CASCADE, related_name="applications"
    )
    candidate = models.ForeignKey(
        Candidate, on_delete=models.CASCADE, related_name="applications"
    )
    resume = models.FileField(
        upload_to=resume_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=["pdf", "doc", "docx"])],
        help_text="Resume file (PDF, DOC, or DOCX, max 5MB).",
    )
    cover_letter = models.TextField(blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.APPLIED
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-applied_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["job", "candidate"], name="unique_job_candidate_application"
            )
        ]

    def __str__(self):
        return f"{self.candidate.full_name} -> {self.job.title} ({self.get_status_display()})"
