// Client-side validation for the job application modal.
// This complements (never replaces) Django's server-side form validation.
(function () {
    const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[A-Za-z]{2,}$/;
    const PHONE_RE = /^[0-9+\-\s()]{7,20}$/;
    const URL_RE = /^(https?:\/\/)[^\s]+\.[^\s]{2,}$/i;

    const MAX_SKILLS_LENGTH = 500;
    const MAX_COVER_LETTER_LENGTH = 3000;
    const MAX_RESUME_SIZE_BYTES = 5 * 1024 * 1024; // 5MB
    const ALLOWED_RESUME_EXTENSIONS = ["pdf", "doc", "docx"];

    function showError(field, message) {
        field.classList.add("is-invalid");
        const feedback = field.parentElement.querySelector(".invalid-feedback");
        if (feedback) feedback.textContent = message;
    }

    function clearError(field) {
        field.classList.remove("is-invalid");
        const feedback = field.parentElement.querySelector(".invalid-feedback");
        if (feedback) feedback.textContent = "";
    }

    function validateForm(form) {
        let isValid = true;

        const fullName = form.querySelector("[name='full_name']");
        const email = form.querySelector("[name='email']");
        const phone = form.querySelector("[name='phone']");
        const portfolioUrl = form.querySelector("[name='portfolio_url']");
        const skills = form.querySelector("[name='skills']");
        const resume = form.querySelector("[name='resume']");
        const coverLetter = form.querySelector("[name='cover_letter']");

        if (fullName) {
            const value = fullName.value.trim();
            if (value.length < 2) {
                showError(fullName, "Please enter your full name.");
                isValid = false;
            } else {
                clearError(fullName);
            }
        }

        if (email) {
            const value = email.value.trim();
            if (!value || !EMAIL_RE.test(value)) {
                showError(email, "Please enter a valid email address.");
                isValid = false;
            } else {
                clearError(email);
            }
        }

        if (phone) {
            const value = phone.value.trim();
            const digitCount = (value.match(/\d/g) || []).length;
            if (!value || !PHONE_RE.test(value) || digitCount < 7 || digitCount > 15) {
                showError(phone, "Please enter a valid phone number.");
                isValid = false;
            } else {
                clearError(phone);
            }
        }

        if (portfolioUrl) {
            const value = portfolioUrl.value.trim();
            if (value && !URL_RE.test(value)) {
                showError(portfolioUrl, "Please enter a valid URL (starting with http:// or https://).");
                isValid = false;
            } else {
                clearError(portfolioUrl);
            }
        }

        if (skills) {
            const value = skills.value.trim();
            if (!value) {
                showError(skills, "Please list at least one skill.");
                isValid = false;
            } else if (value.length > MAX_SKILLS_LENGTH) {
                showError(skills, `Please keep skills under ${MAX_SKILLS_LENGTH} characters.`);
                isValid = false;
            } else {
                clearError(skills);
            }
        }

        if (resume) {
            const file = resume.files && resume.files[0];
            if (!file) {
                showError(resume, "Please upload your resume.");
                isValid = false;
            } else {
                const extension = file.name.includes(".")
                    ? file.name.split(".").pop().toLowerCase()
                    : "";
                if (!ALLOWED_RESUME_EXTENSIONS.includes(extension)) {
                    showError(resume, "Please upload a PDF, DOC, or DOCX file.");
                    isValid = false;
                } else if (file.size > MAX_RESUME_SIZE_BYTES) {
                    showError(resume, "Resume file must be 5MB or smaller.");
                    isValid = false;
                } else {
                    clearError(resume);
                }
            }
        }

        if (coverLetter) {
            const value = coverLetter.value.trim();
            if (value.length > MAX_COVER_LETTER_LENGTH) {
                showError(coverLetter, `Please keep your cover letter under ${MAX_COVER_LETTER_LENGTH} characters.`);
                isValid = false;
            } else {
                clearError(coverLetter);
            }
        }

        return isValid;
    }

    document.querySelectorAll("[data-application-form]").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            if (!validateForm(form)) {
                event.preventDefault();
                event.stopPropagation();
            }
        });

        form.querySelectorAll("input, textarea").forEach(function (field) {
            field.addEventListener("blur", function () {
                validateForm(form);
            });
        });
    });
})();
