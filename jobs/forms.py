from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Candidate

MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024  # 5MB
ALLOWED_RESUME_EXTENSIONS = ("pdf", "doc", "docx")


class UserRegistrationForm(UserCreationForm):
    """
    Sign-up form for new site accounts (job seekers).

    Wraps Django's built-in UserCreationForm (which already handles
    username + password confirmation + password validation) and adds a
    required, unique email address on top of it.
    """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": "you@example.com"}
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Choose a username"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Create a password"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Confirm password"}
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class JobApplicationForm(forms.ModelForm):
    """
    Combined candidate + application form used on the "Apply Now" modal.

    This is a ModelForm bound to Candidate (full_name, email, phone,
    portfolio_url, skills) with additional resume and cover_letter fields
    for the JobApplication. The job posting and application status are
    never exposed to the user -- they are always assigned by the view.
    """

    resume = forms.FileField(
        required=True,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": ".pdf,.doc,.docx",
            }
        ),
        help_text="PDF, DOC, or DOCX — max 5MB.",
    )

    cover_letter = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 5,
                "class": "form-control",
                "placeholder": "Tell us why you're a great fit for this role (optional)",
                "maxlength": "3000",
            }
        ),
        max_length=3000,
    )

    class Meta:
        model = Candidate
        fields = ["full_name", "email", "phone", "portfolio_url", "skills"]
        widgets = {
            "full_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Full name"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "you@example.com"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+91 98765 43210"}
            ),
            "portfolio_url": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://your-portfolio.example.com (optional)",
                }
            ),
            "skills": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. Python, Django, REST APIs",
                    "maxlength": "500",
                }
            ),
        }

    def clean_full_name(self):
        full_name = self.cleaned_data["full_name"].strip()
        if len(full_name) < 2:
            raise forms.ValidationError("Please enter your full name.")
        return full_name

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = [ch for ch in phone if ch.isdigit()]
        if len(digits) < 7:
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone

    def clean_skills(self):
        skills = self.cleaned_data["skills"].strip()
        if not skills:
            raise forms.ValidationError("Please list at least one skill.")
        return skills

    def clean_email(self):
        return self.cleaned_data["email"].strip().lower()

    def clean_resume(self):
        resume = self.cleaned_data["resume"]

        extension = resume.name.rsplit(".", 1)[-1].lower() if "." in resume.name else ""
        if extension not in ALLOWED_RESUME_EXTENSIONS:
            raise forms.ValidationError(
                "Please upload your resume as a PDF, DOC, or DOCX file."
            )

        if resume.size > MAX_RESUME_SIZE_BYTES:
            raise forms.ValidationError("Resume file must be 5MB or smaller.")

        return resume

    def validate_unique(self):
        # Candidate.email is unique, but a returning candidate applying to a
        # *different* job is expected and handled explicitly in the view
        # (get_or_create by email + a separate JobApplication uniqueness
        # check). Skip Django's automatic "Candidate with this Email already
        # exists" validation here so this ModelForm can be reused for both
        # brand-new and returning candidates.
        pass
