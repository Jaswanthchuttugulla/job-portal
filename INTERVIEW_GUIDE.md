# HireLine — Job Board & ATS: Interview Prep Guide

This document walks through the whole project so you can explain it confidently in an interview. It covers architecture, every file's purpose, the design decisions behind it, and a Q&A section with the kind of questions an interviewer is likely to ask.

---

## 1. One-line pitch

> "HireLine is a Django job board with a built-in Applicant Tracking System (ATS). Job seekers browse postings and apply with a resume, and recruiters (staff users) manage applications through a dashboard and a Kanban-style pipeline."

---

## 2. Tech stack

| Layer | Choice | Why it matters to mention |
|---|---|---|
| Backend framework | Django 5 | Batteries-included: ORM, auth, admin, forms, migrations |
| Database | SQLite (dev) / Postgres via `dj-database-url` (prod, e.g. Render) | Easy local dev, production-ready swap with one env var |
| Static files | WhiteNoise | Serves compressed, hashed static files without a separate CDN/nginx in front |
| Frontend | Server-rendered Django templates + Bootstrap 5 + vanilla JS | No SPA/build step — keeps the project simple and fully understandable |
| Deployment | `render.yaml` (Render.com) | Infrastructure-as-code for the hosting platform |

---

## 3. Project layout

```
jobboard_ats/
├── jobboard_ats/          # Django "project" package (settings/urls/wsgi)
│   ├── settings.py
│   └── urls.py
├── jobs/                   # The single Django "app" — all business logic lives here
│   ├── models.py           # Company, JobPosting, Candidate, JobApplication
│   ├── forms.py            # JobApplicationForm, UserRegistrationForm
│   ├── views.py            # Public views + staff-only recruiter views
│   ├── urls.py              # App-level URL routing
│   ├── admin.py             # Django admin registration
│   ├── migrations/          # Versioned schema history
│   ├── management/commands/seed_demo_data.py  # `python manage.py seed_demo_data`
│   ├── static/jobs/         # CSS + JS (no build tooling — plain files)
│   └── templates/jobs/      # HTML templates
├── manage.py
└── requirements.txt
```

**Why one app ("jobs") instead of several?** The domain is small and tightly coupled (jobs, candidates, applications all reference each other constantly), so splitting into `jobs`, `candidates`, `applications` apps would add import complexity without a real benefit at this size. This is a legitimate trade-off to mention: "I'd split it into more apps once distinct bounded contexts emerge, e.g. a separate `accounts` app once auth grows."

---

## 4. Data model (`jobs/models.py`)

### `Company`
Just a company profile (name, website, location, logo). One company → many job postings.

### `JobPosting`
- `job_type` uses Django's `TextChoices` — an enum-like pattern that keeps valid values, human-readable labels, and DB storage in one place, and gives you `JobPosting.JobType.FULL_TIME` instead of magic strings.
- `required_skills` is a comma-separated `CharField` with a `skills_list()` helper method rather than a separate `Skill` model + M2M. This is a deliberate simplicity/normalization trade-off — good to be able to defend in an interview: *"I chose a denormalized CSV field because skill search here is just an `icontains` filter, not exact matching or skill-based analytics. If we needed real skill taxonomy or matching, I'd normalize into a `Skill` model with a `ManyToManyField`."*
- `is_active` lets a job be "closed" without deleting history (soft state, not deletion).

### `Candidate`
A job seeker's identity, keyed by a **unique email** — this is the crux of a subtle design decision (see `apply_to_job` below): a candidate is *not* a login-based `User` account. They're identified by email across multiple applications, guest-checkout style.

### `JobApplication`
The join between `JobPosting` and `Candidate`, plus:
- `status` — a `TextChoices` state machine: `APPLIED → REVIEW → SHORTLIST` or `REJECTED`. This is the backbone of the ATS Kanban board.
- `resume` — a `FileField` (added in this update) with:
  - `upload_to=resume_upload_path` — a **callable**, not a static string, so each file gets a unique, human-readable path (`resumes/2026/07/jane-doe_20260708123456.pdf`). Callables are the standard way to avoid filename collisions and to keep uploads organized by date.
  - `validators=[FileExtensionValidator(...)]` — model-level validation as a safety net *in addition to* form-level validation (defense in depth: the form validates on the way in, but the model validator protects anything that creates a `JobApplication` directly, e.g. the Django admin or a future API).
- A `UniqueConstraint` on `(job, candidate)` — enforced at the **database** level, not just in Python — so a race condition (two simultaneous submits) still can't create duplicate applications. This is paired with `IntegrityError` handling in the view (see below) — a good interview point: *"I don't rely on a pre-check-then-insert pattern alone, because that has a TOCTOU race condition; the DB constraint is the actual source of truth, and the view catches the resulting `IntegrityError` as a UX-level fallback."*

---

## 5. Forms (`jobs/forms.py`)

### `JobApplicationForm(forms.ModelForm)`
- Bound to the `Candidate` model (`full_name`, `email`, `phone`, `portfolio_url`, `skills`), **plus** two fields that don't belong to `Candidate` at all: `resume` and `cover_letter` (these belong to `JobApplication`). This is a common, useful pattern: **one form representing two models**, because from the user's point of view it's a single "Apply" action, even though it results in two DB writes.
- Custom `clean_<field>` methods (`clean_full_name`, `clean_phone`, `clean_skills`, `clean_email`, `clean_resume`) — each returns the cleaned value or raises `forms.ValidationError`. This is Django's standard per-field validation hook, always named `clean_<fieldname>`.
- `clean_resume` checks file **extension** and **size** — note validation happens twice (client-side in JS for instant feedback, server-side in the form because JS can always be bypassed). Good interview line: *"Client-side validation is a UX nicety; server-side validation is the actual security boundary."*
- `validate_unique()` is overridden to a no-op. Why? Because `Candidate.email` is `unique=True`, Django's default `ModelForm` behavior would reject the form outright the moment an *existing* candidate (identified by email) tries to apply again — but that's actually the expected, supported flow (a returning candidate applying to a second job). The real "already applied to *this specific job*" check is done explicitly in the view instead, against `(job, candidate)`, which is the constraint that actually matters.

### `UserRegistrationForm(UserCreationForm)`
- Extends Django's **built-in** `UserCreationForm` rather than writing password-confirmation/hashing logic from scratch — a strong interview point: *"I reuse Django's battle-tested auth forms instead of rolling my own password handling."*
- Adds a required, uniqueness-checked `email` field on top (vanilla `UserCreationForm` only requires `username` + password).
- Overrides `save()` to also set `user.email` before saving, since the base form's `Meta.fields` doesn't include email by default in older Django patterns.

---

## 6. Views (`jobs/views.py`)

The file is split into two clearly-commented sections: **Public views** and **Recruiter (staff-only) views** — worth mentioning that this separation itself is a form of documentation.

### Public views
- `JobListView` (class-based `ListView`) — handles search/filter via query params (`q`, `skill`, `location`, `job_type`) directly in `get_queryset()`. Uses `Q` objects for OR-style search across title/description/company name.
- `JobDetailView` (class-based `DetailView`) — only returns `is_active=True` jobs (`get_queryset` override), so an inactive job 404s for the public even if the recruiter can still see it in the dashboard. Injects a blank `JobApplicationForm` into context for the apply modal.
- `apply_to_job` (function-based view) — the most important view to be able to narrate line-by-line:
  1. `@require_POST` — GET requests to this URL are rejected (405), since applying is a mutation.
  2. `get_object_or_404(..., is_active=True)` — can't apply to a closed/nonexistent job.
  3. `JobApplicationForm(request.POST, request.FILES)` — **note both `POST` and `FILES`**; file uploads never appear in `request.POST`, they're a separate dict, and forgetting `request.FILES` here is the single most common bug when adding file uploads to a Django form.
  4. `transaction.atomic()` wraps the "get-or-create candidate, then create application" logic so it's all-or-nothing — if creating the `JobApplication` fails, the candidate record isn't left in a half-updated state.
  5. `Candidate.objects.get_or_create(email=..., defaults={...})` then, if not newly created, manually updates the existing candidate's fields — this "upsert" pattern keeps the candidate's profile fresh across multiple applications.
  6. An explicit `.filter(job=job, candidate=candidate).exists()` check gives a friendly error message in the common case, and the `except IntegrityError` around the whole block catches the rare race-condition case where two requests slip past that check simultaneously.
  7. On success, redirects (not renders) — **Post/Redirect/Get pattern** — so refreshing the success page doesn't resubmit the form.
- `register` (function-based view, new) — follows the same GET/POST-branch structure as a typical Django auth view: GET shows a blank form, POST validates + creates the `User` + logs them in immediately (`login(request, user)`) + redirects. Guards against already-authenticated users hitting the page.
- `application_success` — a simple confirmation page, looked up by `?job=<id>` in the query string.

### Recruiter (staff-only) views
- `StaffRequiredMixin(UserPassesTestMixin)` — a **reusable mixin**, not copy-pasted permission checks, applied to every recruiter view. `test_func()` defines the rule (`is_staff_user`); `handle_no_permission()` customizes the redirect behavior (logged-in-but-not-staff → friendly error + redirect; anonymous → login page). This is the cleanest way to DRY up authorization in Django CBVs.
- `RecruiterDashboardView` — filterable, paginated table of all applications, plus aggregate counts per status using `.annotate(Count(...))` — a good example of doing aggregation in the database rather than in Python loops.
- `AtsPipelineView` — same queryset idea, but groups applications into four Python lists by status for the Kanban board template.
- `update_application_status` — a good one to know cold:
  - `@user_passes_test` + `@require_POST` stacked decorators — staff-only *and* POST-only.
  - Validates `new_status` against `JobApplication.Status.choices` **server-side**, never trusting the client — even though the `<select>` in the HTML only offers valid options, someone could still POST an arbitrary string directly.
  - Detects AJAX vs regular form submission via the `X-Requested-With` header and returns `JsonResponse` or a redirect accordingly — supports both the fetch()-based Kanban drag/update AND a plain HTML fallback.

---

## 7. URLs (`jobs/urls.py`)

Straightforward `path()` list; a few points worth calling out:
- Auth views (`login`, `logout`) reuse Django's **built-in** `django.contrib.auth.views` classes rather than writing view logic for them — only the template is customized.
- URL names (`job_list`, `job_detail`, `apply_to_job`, etc.) are used everywhere via `{% url %}` in templates and `reverse()`/`redirect()` in views — never hardcoded paths — so the URL structure can change without breaking links.

---

## 8. Templates & static assets

- `base.html` — shared layout: navbar (with conditional staff-only links + the new "Sign Up" link), theme toggle, block structure (`{% block title %}`, `{% block content %}`).
- `_apply_modal.html` and `_kanban_column.html` — **partial templates**, `{% include %}`-ed rather than duplicated, since the apply modal appears on every job detail page and the kanban column repeats four times (once per status).
- `application.js` — client-side validation that **mirrors** (never replaces) the server-side `clean_*` methods in `forms.py` — the comment at the top of the file says this explicitly. Good interview point: *"Client validation and server validation should express the same rules; if they drift, that's a bug waiting to be exploited or a confusing UX inconsistency."*
- `recruiter_dashboard.js` — the AJAX status-update logic that talks to `update_application_status`.

---

## 9. The resume-upload feature, end to end (what was added)

Trace this whole path out loud in an interview — it demonstrates you understand the full request/response cycle:

1. **Model**: `JobApplication.resume = models.FileField(upload_to=resume_upload_path, validators=[...])`
2. **Migration**: `0002_jobapplication_resume.py` adds the column (`AddField`).
3. **Form**: `JobApplicationForm.resume` — required `FileField` + `clean_resume()` enforcing extension + 5MB size limit.
4. **Template**: `_apply_modal.html` gets `enctype="multipart/form-data"` on the `<form>` tag (**mandatory** for file uploads — without it, the browser silently won't send the file bytes at all) and a `<input type="file" name="resume">`.
5. **Client JS**: `application.js` checks the file exists, has an allowed extension, and is under 5MB, before letting the form submit.
6. **View**: `apply_to_job` reads `request.FILES`, and `JobApplication.objects.create(resume=form.cleaned_data["resume"], ...)` — Django's `FileField` + default `FileSystemStorage` backend handles writing the actual bytes to disk (or S3/etc. in production) using the upload path we defined.
7. **Settings**: `MEDIA_URL` / `MEDIA_ROOT` tell Django where uploaded files live and what URL prefix serves them; `urls.py` adds `static(settings.MEDIA_URL, ...)` **only when `DEBUG=True`** — in production, a real web server or storage backend (e.g. S3) should serve media, not Django itself.
8. **Recruiter-facing surface**: resume download links added to the dashboard table, the Kanban cards, and Django admin, so the upload is actually usable, not just stored.

If asked *"why FileField and not something else?"*: `FileField` (and its `ImageField` subclass) is Django's abstraction over pluggable storage backends — the same model code works whether files land on local disk (dev) or S3/GCS (prod), because the storage backend is swapped via `STORAGES["default"]` in settings, not by changing model or view code.

If asked *"how would you scale this?"*: virus-scan uploads before accepting them, move storage to S3 with a private bucket + signed URLs instead of public media serving, and possibly parse resumes (e.g. extract skills) asynchronously via a task queue (Celery) rather than blocking the request.

---

## 10. The new registration feature

- `UserRegistrationForm` — thin wrapper around `UserCreationForm` (see §5).
- `register` view — GET/POST branch, redirects already-authenticated users away, logs the new user in immediately on success (no separate "verify your email" step — a reasonable simplification to name explicitly if asked, since a production system would likely add email verification).
- New users are **not** staff by default (`User.is_staff` defaults to `False`), so registering does *not* grant access to the recruiter dashboard — that still requires an account explicitly marked staff (via Django admin or `createsuperuser`). This separation is important to be able to explain: *"regular signup" vs "staff/recruiter access"* are two different privilege tiers, and the `StaffRequiredMixin` is what enforces that boundary.

---

## 11. Likely interview questions & how to answer them

**Q: Why class-based views for some things and function-based for others?**
A: CBVs (`ListView`, `DetailView`) fit the standard "list a queryset" / "show one object" patterns almost for free. `apply_to_job`, `register`, and `update_application_status` have bespoke, multi-step logic (transactions, file handling, AJAX-vs-regular branching) that reads more clearly as an explicit function than by overriding several CBV hook methods.

**Q: How do you prevent a candidate applying twice to the same job?**
A: Two layers — a DB-level `UniqueConstraint(job, candidate)` (the actual guarantee, race-condition-safe) plus a friendlier explicit `.exists()` check in the view for the common case, with `IntegrityError` as the safety net for the rare concurrent case.

**Q: How is authorization enforced for the recruiter dashboard?**
A: `StaffRequiredMixin` (a `UserPassesTestMixin` subclass) on every recruiter CBV, and `@user_passes_test` decorator on the one recruiter FBV. Both check `user.is_authenticated and user.is_staff`.

**Q: Why validate file uploads both client- and server-side?**
A: Client-side is UX (immediate feedback, no round trip). Server-side (`clean_resume`, plus the model's `FileExtensionValidator`) is the actual security/data-integrity boundary, since client-side checks can always be bypassed (disabled JS, direct POST via curl, etc.).

**Q: What happens if `enctype="multipart/form-data"` is missing from the form?**
A: The browser submits the form as normal URL-encoded data and simply **omits the file's contents** — `request.FILES` would be empty and the form would fail validation on the required `resume` field, with no obvious error explaining why.

**Q: How would you add resume parsing / auto-skill-extraction?**
A: Keep the upload synchronous and fast (as now); on save, enqueue an async task (Celery/RQ) that reads the file, extracts text (e.g. via `pdfplumber`/`python-docx`), and updates `Candidate.skills` or a new `parsed_resume_text` field — never parse in the request/response cycle itself, since parsing can be slow or fail.

**Q: Why not let a Candidate log in and see "my applications"?**
A: Current design intentionally keeps candidates as guest-checkout-style records keyed by email, to minimize friction on the apply flow. Adding candidate accounts (linking `Candidate` to a `User` via a `OneToOneField`) would be the natural next step if a "track my applications" dashboard were required — and the newly-added registration system is a first step toward that, though it isn't yet wired into the `Candidate` model.

---

## 12. Quick command reference

```bash
python manage.py migrate            # apply schema changes
python manage.py createsuperuser    # create a staff/admin account
python manage.py seed_demo_data     # populate sample jobs/companies
python manage.py runserver          # run locally
```
