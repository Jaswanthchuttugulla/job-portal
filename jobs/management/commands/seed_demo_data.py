"""
Optional convenience command for local development only.

Seeds the database with a handful of companies and job postings so the
job board isn't empty the first time you run the project. This writes
real rows through the Django ORM (not template mock data) and is safe
to run multiple times - it uses get_or_create.

Usage:
    python manage.py seed_demo_data
"""

import datetime

from django.core.management.base import BaseCommand

from jobs.models import Company, JobPosting


class Command(BaseCommand):
    help = "Seed the database with sample companies and job postings for local development."

    def handle(self, *args, **options):
        companies_data = [
            {
                "name": "Nimbus Cloud Systems",
                "website": "https://example-nimbus.com",
                "location": "Hyderabad, India",
                "logo_url": "",
            },
            {
                "name": "Bluewave Analytics",
                "website": "https://example-bluewave.com",
                "location": "Bengaluru, India",
                "logo_url": "",
            },
            {
                "name": "Northbridge Studio",
                "website": "https://example-northbridge.com",
                "location": "Remote",
                "logo_url": "",
            },
        ]

        companies = {}
        for data in companies_data:
            company, _ = Company.objects.get_or_create(
                name=data["name"], defaults=data
            )
            companies[data["name"]] = company

        deadline = datetime.date.today() + datetime.timedelta(days=30)

        jobs_data = [
            {
                "company": companies["Nimbus Cloud Systems"],
                "title": "Backend Engineer (Django)",
                "job_type": JobPosting.JobType.FULL_TIME,
                "location": "Hyderabad, India",
                "required_skills": "Python, Django, PostgreSQL, REST APIs",
                "salary_range": "₹12,00,000 - ₹18,00,000 / year",
                "description": (
                    "Build and maintain backend services powering our cloud "
                    "platform. Work closely with product and DevOps teams."
                ),
                "application_deadline": deadline,
                "is_active": True,
            },
            {
                "company": companies["Bluewave Analytics"],
                "title": "Data Analyst Intern",
                "job_type": JobPosting.JobType.INTERNSHIP,
                "location": "Bengaluru, India",
                "required_skills": "SQL, Python, Excel, Data Visualization",
                "salary_range": "₹25,000 / month stipend",
                "description": (
                    "Assist the analytics team with reporting dashboards, "
                    "data cleaning, and ad-hoc analysis for client accounts."
                ),
                "application_deadline": deadline,
                "is_active": True,
            },
            {
                "company": companies["Northbridge Studio"],
                "title": "Remote Frontend Developer",
                "job_type": JobPosting.JobType.REMOTE,
                "location": "Remote",
                "required_skills": "JavaScript, HTML, CSS, Bootstrap",
                "salary_range": "$60,000 - $80,000 / year",
                "description": (
                    "Own the frontend of our marketing sites and internal "
                    "tools. Comfortable with responsive, accessible UI."
                ),
                "application_deadline": deadline,
                "is_active": True,
            },
        ]

        created_count = 0
        for data in jobs_data:
            _, created = JobPosting.objects.get_or_create(
                title=data["title"], company=data["company"], defaults=data
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Seed complete. {len(companies)} companies ensured, "
                f"{created_count} new job postings created."
            )
        )
