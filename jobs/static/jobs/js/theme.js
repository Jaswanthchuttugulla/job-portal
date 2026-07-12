// Dark mode toggle with localStorage persistence.
(function () {
    const STORAGE_KEY = "hireline-theme";
    const root = document.documentElement;
    const toggleBtn = document.getElementById("themeToggle");

    function applyIcon(theme) {
        if (!toggleBtn) return;
        const icon = toggleBtn.querySelector("i");
        if (!icon) return;
        icon.className = theme === "dark" ? "bi bi-sun-fill" : "bi bi-moon-stars-fill";
    }

    function getCurrentTheme() {
        return root.getAttribute("data-theme") === "dark" ? "dark" : "light";
    }

    // Sync icon with whatever the early inline script already applied.
    applyIcon(getCurrentTheme());

    if (toggleBtn) {
        toggleBtn.addEventListener("click", function () {
            const next = getCurrentTheme() === "dark" ? "light" : "dark";
            root.setAttribute("data-theme", next);
            applyIcon(next);
            try {
                localStorage.setItem(STORAGE_KEY, next);
            } catch (e) {
                // localStorage unavailable (private browsing, etc.) - theme
                // will simply not persist across reloads.
            }
        });
    }
})();
