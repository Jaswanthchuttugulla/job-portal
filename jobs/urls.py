from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path("", views.JobListView.as_view(), name="job_list"),
    path("jobs/<int:pk>/", views.JobDetailView.as_view(), name="job_detail"),
    path("jobs/<int:job_id>/apply/", views.apply_to_job, name="apply_to_job"),
    path("application/success/", views.application_success, name="application_success"),
    path("register/", views.register, name="register"),
    path(
        "recruiter/login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path(
        "recruiter/logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path(
        "recruiter/dashboard/",
        views.RecruiterDashboardView.as_view(),
        name="recruiter_dashboard",
    ),
    path(
        "recruiter/pipeline/",
        views.AtsPipelineView.as_view(),
        name="ats_pipeline",
    ),
    path(
        "recruiter/applications/<int:pk>/status/",
        views.update_application_status,
        name="update_application_status",
    ),
]
