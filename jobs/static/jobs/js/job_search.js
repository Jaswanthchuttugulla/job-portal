// Real-time client-side filtering of job cards already rendered on the page.
// This is a progressive enhancement layer: server-side GET filtering
// (see views.JobListView) already works without JavaScript.
(function () {
    const input = document.getElementById("liveFilterInput");
    const cards = document.querySelectorAll("[data-job-card]");
    const emptyState = document.getElementById("liveFilterEmptyState");

    if (!input || cards.length === 0) return;

    function normalize(text) {
        return (text || "").toLowerCase().trim();
    }

    input.addEventListener("input", function () {
        const term = normalize(input.value);
        let visibleCount = 0;

        cards.forEach(function (card) {
            const haystack = normalize(
                (card.dataset.title || "") + " " +
                (card.dataset.company || "") + " " +
                (card.dataset.location || "") + " " +
                (card.dataset.skills || "")
            );

            const isMatch = term === "" || haystack.includes(term);
            card.closest(".hl-job-col").style.display = isMatch ? "" : "none";
            if (isMatch) visibleCount += 1;
        });

        if (emptyState) {
            emptyState.classList.toggle("d-none", visibleCount !== 0);
        }
    });
})();
