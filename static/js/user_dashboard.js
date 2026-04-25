document.addEventListener("DOMContentLoaded", () => {
    bindUserSections();
});

function bindUserSections() {
    const controls = document.querySelectorAll("[data-user-section]");
    if (!controls.length) {
        return;
    }

    const sectionIds = new Set(
        [...controls]
            .map((control) => control.dataset.userSection)
            .filter(Boolean)
    );

    const showSection = (sectionName, syncHash = true) => {
        const safeSection = sectionIds.has(sectionName) ? sectionName : "home";

        document.querySelectorAll(".user-section").forEach((section) => {
            section.classList.toggle("active", section.id === `user-section-${safeSection}`);
        });

        controls.forEach((control) => {
            control.classList.toggle("active", control.dataset.userSection === safeSection);
        });

        if (syncHash) {
            window.history.replaceState(null, "", `#${safeSection}`);
        }
    };

    controls.forEach((control) => {
        control.addEventListener("click", () => {
            showSection(control.dataset.userSection);
        });
    });

    const requested = window.location.hash.replace("#", "").trim();
    showSection(requested || "home", false);
}
