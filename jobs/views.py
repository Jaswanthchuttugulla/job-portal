from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST, require_http_methods
from django.views.generic import DetailView, ListView

from .forms import JobApplicationForm, UserRegistrationForm
from .models import Candidate, JobApplication, JobPosting


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


# ---------------------------------------------------------------------------
# Public views
# ---------------------------------------------------------------------------


@require_http_methods(["GET", "POST"])
def register(request):
    """Sign-up page for new (non-staff) site accounts."""

    if request.user.is_authenticated:
        return redirect("job_list")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome, {user.username}! Your account has been created.")
            return redirect("job_list")
    else:
        form = UserRegistrationForm()

    return render(request, "registration/register.html", {"form": form})


class JobListView(ListView):
    """Public home page: browse, search, and filter active job postings."""

    model = JobPosting
    template_name = "jobs/home.html"
    context_object_name = "jobs"
    paginate_by = 9

    def get_queryset(self):
        queryset = JobPosting.objects.filter(is_active=True).select_related("company")

        query = self.request.GET.get("q", "").strip()
        skill = self.request.GET.get("skill", "").strip()
        location = self.request.GET.get("location", "").strip()
        job_type = self.request.GET.get("job_type", "").strip()

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(company__name__icontains=query)
            )

        if skill:
            queryset = queryset.filter(required_skills__icontains=skill)

        if location:
            queryset = queryset.filter(location__icontains=location)

        if job_type:
            queryset = queryset.filter(job_type=job_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["skill"] = self.request.GET.get("skill", "")
        context["location"] = self.request.GET.get("location", "")
        context["job_type"] = self.request.GET.get("job_type", "")
        context["job_type_choices"] = JobPosting.JobType.choices
        context["total_active_jobs"] = JobPosting.objects.filter(is_active=True).count()
        return context


class JobDetailView(DetailView):
    """Public job detail page. Inactive jobs are not publicly accessible."""

    model = JobPosting
    template_name = "jobs/job_detail.html"
    context_object_name = "job"

    def get_queryset(self):
        return JobPosting.objects.filter(is_active=True).select_related("company")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = JobApplicationForm()
        return context


@require_POST
def apply_to_job(request, job_id):
    """Handle submission of the job-application modal form."""

    job = get_object_or_404(JobPosting, pk=job_id, is_active=True)
    form = JobApplicationForm(request.POST, request.FILES)

    if not form.is_valid():
        # Re-render the job detail page with the bound (invalid) form so
        # the user sees inline validation errors from the server side.
        return render(
            request,
            "jobs/job_detail.html",
            {"job": job, "form": form, "form_has_errors": True},
        )

    email = form.cleaned_data["email"].strip().lower()

    try:
        with transaction.atomic():
            candidate, created = Candidate.objects.get_or_create(
                email=email,
                defaults={
                    "full_name": form.cleaned_data["full_name"],
                    "phone": form.cleaned_data["phone"],
                    "portfolio_url": form.cleaned_data["portfolio_url"],
                    "skills": form.cleaned_data["skills"],
                },
            )

            if not created:
                # Keep the candidate's profile reasonably up to date.
                candidate.full_name = form.cleaned_data["full_name"]
                candidate.phone = form.cleaned_data["phone"]
                if form.cleaned_data["portfolio_url"]:
                    candidate.portfolio_url = form.cleaned_data["portfolio_url"]
                candidate.skills = form.cleaned_data["skills"]
                candidate.save()

            if JobApplication.objects.filter(job=job, candidate=candidate).exists():
                messages.error(
                    request,
                    "You have already applied to this job with this email address.",
                )
                return redirect("job_detail", pk=job.pk)

            JobApplication.objects.create(
                job=job,
                candidate=candidate,
                resume=form.cleaned_data["resume"],
                cover_letter=form.cleaned_data.get("cover_letter", ""),
                status=JobApplication.Status.APPLIED,
            )
    except IntegrityError:
        messages.error(
            request,
            "You have already applied to this job with this email address.",
        )
        return redirect("job_detail", pk=job.pk)

    return redirect(f"{reverse('application_success')}?job={job.pk}")


def application_success(request):
    job_id = request.GET.get("job")
    job = JobPosting.objects.filter(pk=job_id).select_related("company").first()
    return render(request, "jobs/application_success.html", {"job": job})


# ---------------------------------------------------------------------------
# Recruiter (staff-only) views
# ---------------------------------------------------------------------------


class StaffRequiredMixin(UserPassesTestMixin):
    """Only authenticated staff users may access the view."""

    login_url = "login"

    def test_func(self):
        return is_staff_user(self.request.user)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(
                self.request, "You do not have permission to access the recruiter area."
            )
            return redirect("job_list")
        return super().handle_no_permission()


class RecruiterDashboardView(StaffRequiredMixin, ListView):
    """Recruiter dashboard: summary statistics + filterable applications table."""

    model = JobApplication
    template_name = "jobs/recruiter_dashboard.html"
    context_object_name = "applications"
    paginate_by = 15

    def get_queryset(self):
        queryset = JobApplication.objects.select_related(
            "job", "job__company", "candidate"
        )

        job_id = self.request.GET.get("job", "").strip()
        candidate_query = self.request.GET.get("candidate", "").strip()
        status = self.request.GET.get("status", "").strip()

        if job_id:
            queryset = queryset.filter(job_id=job_id)

        if candidate_query:
            queryset = queryset.filter(
                Q(candidate__full_name__icontains=candidate_query)
                | Q(candidate__email__icontains=candidate_query)
            )

        if status:
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        all_applications = JobApplication.objects.all()
        status_counts = dict(
            all_applications.values_list("status").annotate(count=Count("id"))
        )

        context["total_applications"] = all_applications.count()
        context["applied_count"] = status_counts.get(JobApplication.Status.APPLIED, 0)
        context["review_count"] = status_counts.get(JobApplication.Status.REVIEW, 0)
        context["shortlist_count"] = status_counts.get(JobApplication.Status.SHORTLIST, 0)
        context["rejected_count"] = status_counts.get(JobApplication.Status.REJECTED, 0)

        context["jobs"] = JobPosting.objects.all().order_by("-posted_date")
        context["status_choices"] = JobApplication.Status.choices

        context["selected_job"] = self.request.GET.get("job", "")
        context["candidate_query"] = self.request.GET.get("candidate", "")
        context["selected_status"] = self.request.GET.get("status", "")

        return context


class AtsPipelineView(StaffRequiredMixin, ListView):
    """Kanban-style ATS pipeline showing candidates grouped by status."""

    model = JobApplication
    template_name = "jobs/ats_pipeline.html"
    context_object_name = "applications"

    def get_queryset(self):
        queryset = JobApplication.objects.select_related(
            "job", "job__company", "candidate"
        )
        job_id = self.request.GET.get("job", "").strip()
        if job_id:
            queryset = queryset.filter(job_id=job_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        applications = context["applications"]

        context["applied"] = [a for a in applications if a.status == JobApplication.Status.APPLIED]
        context["review"] = [a for a in applications if a.status == JobApplication.Status.REVIEW]
        context["shortlist"] = [a for a in applications if a.status == JobApplication.Status.SHORTLIST]
        context["rejected"] = [a for a in applications if a.status == JobApplication.Status.REJECTED]

        context["jobs"] = JobPosting.objects.all().order_by("-posted_date")
        context["selected_job"] = self.request.GET.get("job", "")
        context["status_choices"] = JobApplication.Status.choices
        return context


@user_passes_test(is_staff_user, login_url="login")
@require_POST
def update_application_status(request, pk):
    """
    Securely update a JobApplication's status.

    POST-only, staff-only, CSRF-protected, validates the submitted status
    against the model's declared choices. Supports both AJAX (fetch) and
    regular form-post fallback.
    """

    application = get_object_or_404(JobApplication, pk=pk)
    new_status = request.POST.get("status", "").strip()

    valid_statuses = {choice for choice, _ in JobApplication.Status.choices}
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if new_status not in valid_statuses:
        if is_ajax:
            return JsonResponse({"success": False, "error": "Invalid status."}, status=400)
        messages.error(request, "Invalid status submitted.")
        return redirect("recruiter_dashboard")

    application.status = new_status
    application.save(update_fields=["status"])

    if is_ajax:
        return JsonResponse(
            {
                "success": True,
                "application_id": application.pk,
                "status": application.status,
                "status_display": application.get_status_display(),
            }
        )

    messages.success(request, "Application status updated.")
    next_url = request.POST.get("next") or reverse("recruiter_dashboard")
    return redirect(next_url)
