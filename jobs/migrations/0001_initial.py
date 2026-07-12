import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Company",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=200)),
                ("website", models.URLField(blank=True)),
                ("location", models.CharField(max_length=200)),
                ("logo_url", models.URLField(blank=True)),
            ],
            options={
                "verbose_name": "Company",
                "verbose_name_plural": "Companies",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Candidate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("full_name", models.CharField(max_length=200)),
                ("email", models.EmailField(max_length=254, unique=True)),
                ("phone", models.CharField(max_length=30)),
                ("portfolio_url", models.URLField(blank=True)),
                ("skills", models.CharField(blank=True, max_length=500)),
            ],
            options={
                "ordering": ["full_name"],
            },
        ),
        migrations.CreateModel(
            name="JobPosting",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=200)),
                (
                    "job_type",
                    models.CharField(
                        choices=[
                            ("FULL_TIME", "Full-Time"),
                            ("PART_TIME", "Part-Time"),
                            ("REMOTE", "Remote Work"),
                            ("INTERNSHIP", "Internship"),
                        ],
                        default="FULL_TIME",
                        max_length=20,
                    ),
                ),
                ("location", models.CharField(max_length=200)),
                (
                    "required_skills",
                    models.CharField(
                        help_text="Comma-separated list of skills, e.g. 'Python, Django, SQL'",
                        max_length=500,
                    ),
                ),
                ("salary_range", models.CharField(blank=True, max_length=100)),
                ("description", models.TextField()),
                ("application_deadline", models.DateField()),
                ("is_active", models.BooleanField(default=True)),
                ("posted_date", models.DateTimeField(auto_now_add=True)),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="job_postings",
                        to="jobs.company",
                    ),
                ),
            ],
            options={
                "ordering": ["-posted_date"],
            },
        ),
        migrations.CreateModel(
            name="JobApplication",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("cover_letter", models.TextField(blank=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("APPLIED", "Application Received"),
                            ("REVIEW", "Under HR Review"),
                            ("SHORTLIST", "Shortlisted for Interview"),
                            ("REJECTED", "Not Selected"),
                        ],
                        default="APPLIED",
                        max_length=20,
                    ),
                ),
                ("applied_at", models.DateTimeField(auto_now_add=True)),
                (
                    "candidate",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="applications",
                        to="jobs.candidate",
                    ),
                ),
                (
                    "job",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="applications",
                        to="jobs.jobposting",
                    ),
                ),
            ],
            options={
                "ordering": ["-applied_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="jobapplication",
            constraint=models.UniqueConstraint(
                fields=("job", "candidate"), name="unique_job_candidate_application"
            ),
        ),
    ]
