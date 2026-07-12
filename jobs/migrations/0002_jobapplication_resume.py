import django.core.validators
from django.db import migrations, models

import jobs.models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobapplication",
            name="resume",
            field=models.FileField(
                default="",
                help_text="Resume file (PDF, DOC, or DOCX, max 5MB).",
                upload_to=jobs.models.resume_upload_path,
                validators=[
                    django.core.validators.FileExtensionValidator(
                        allowed_extensions=["pdf", "doc", "docx"]
                    )
                ],
            ),
            preserve_default=False,
        ),
    ]
