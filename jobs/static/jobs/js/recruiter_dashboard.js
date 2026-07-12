// Handles asynchronous ATS status updates from the recruiter dashboard
// table and the Kanban pipeline board, using fetch() + CSRF token.
(function () {
    function getCsrfToken() {
        const input = document.querySelector("[name=csrfmiddlewaretoken]");
        return input ? input.value : "";
    }

    function updateStatus(applicationId, newStatus, onSuccess, onError) {
        const url = `/recruiter/applications/${applicationId}/status/`;

        fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-Requested-With": "XMLHttpRequest",
                "X-CSRFToken": getCsrfToken(),
            },
            body: `status=${encodeURIComponent(newStatus)}`,
        })
            .then(function (response) {
                return response.json().then(function (data) {
                    return { ok: response.ok, data: data };
                });
            })
            .then(function (result) {
                if (result.ok && result.data.success) {
                    onSuccess(result.data);
                } else {
                    onError(result.data.error || "Could not update status.");
                }
            })
            .catch(function () {
                onError("Network error while updating status.");
            });
    }

    // Dropdown-based status updates (table rows + kanban cards share the
    // same [data-status-select] control convention).
    document.querySelectorAll("[data-status-select]").forEach(function (select) {
        select.addEventListener("change", function () {
            const applicationId = select.dataset.applicationId;
            const newStatus = select.value;
            const badge = document.querySelector(
                `[data-status-badge="${applicationId}"]`
            );
            const originalValue = select.dataset.currentStatus;

            select.disabled = true;

            updateStatus(
                applicationId,
                newStatus,
                function (data) {
                    select.disabled = false;
                    select.dataset.currentStatus = data.status;
                    if (badge) {
                        badge.textContent = data.status_display;
                        badge.className = badge.className.replace(
                            /hl-dot-[A-Z]+/,
                            `hl-dot-${data.status}`
                        );
                    }
                    const card = select.closest("[data-candidate-card]");
                    if (card) {
                        card.dataset.status = data.status;
                        card.style.transition = "opacity .2s ease";
                        card.style.opacity = "0.4";
                        setTimeout(function () {
                            window.location.reload();
                        }, 250);
                    }
                },
                function (errorMessage) {
                    select.disabled = false;
                    select.value = originalValue;
                    alert(errorMessage);
                }
            );
        });
    });
})();
