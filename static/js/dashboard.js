document.addEventListener("DOMContentLoaded", function () {
    // ─── Sidebar collapse toggle ──────────────────────────
    const menuBtn = document.getElementById("menu-btn");
    const sidebar = document.querySelector(".sidebar");

    if (menuBtn && sidebar) {
        menuBtn.addEventListener("click", function () {
            sidebar.classList.toggle("sidebar-collapsed");
            // Switch icon
            const icon = this.querySelector("i");
            if (icon) {
                icon.classList.toggle("fa-bars");
                icon.classList.toggle("fa-times");
            }
        });
    }

    // ─── Number counter animation ─────────────────────────
    const statCards = document.querySelectorAll(".dashboard-card h2[data-count]");

    statCards.forEach(function (el) {
        const target = parseInt(el.getAttribute("data-count"), 10);
        if (isNaN(target)) return;

        let current = 0;
        const duration = 1200; // ms
        const stepTime = 40;   // ms per tick
        const steps = Math.ceil(duration / stepTime);
        const increment = target / steps;

        el.textContent = "0";

        const timer = setInterval(function () {
            current += increment;
            if (current >= target) {
                el.textContent = target;
                clearInterval(timer);
            } else {
                el.textContent = Math.floor(current);
            }
        }, stepTime);
    });
});
