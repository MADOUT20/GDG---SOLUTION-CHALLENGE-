const state = {
    dashboard: null,
    activeModal: null,
    mapReady: false,
    pendingRegions: null,
};

const modalConfig = {
    report: {
        formId: "reportForm",
        title: "Log Field Report",
        subtitle: "Add a ground update and push it into the allocation view.",
    },
    donation: {
        formId: "donationForm",
        title: "Register Donation",
        subtitle: "Capture incoming support and reflect its effect on district demand.",
    },
    deployment: {
        formId: "deploymentForm",
        title: "Deploy Volunteers",
        subtitle: "Assign new volunteers to a region and refresh the recommendation table.",
    },
    source: {
        formId: "sourceForm",
        title: "Add Data Batch",
        subtitle: "Connect a fresh source so the aggregated record count stays current.",
    },
};

document.addEventListener("DOMContentLoaded", () => {
    bindTabs();
    bindModal();
    bindForms();
    const initialTab = getInitialTab();
    if (initialTab) {
        showTab(initialTab, { syncHash: false });
    }
    loadDashboard();
});

function bindTabs() {
    document.querySelectorAll("[data-tab]").forEach((button) => {
        button.addEventListener("click", () => showTab(button.dataset.tab));
    });
}

function getInitialTab() {
    const requested = window.location.hash.replace("#", "").trim();
    if (!requested) {
        return "";
    }

    return document.getElementById(requested) ? requested : "";
}

function showTab(tabName, options = {}) {
    if (!document.getElementById(tabName)) {
        return;
    }

    if (options.syncHash !== false) {
        window.history.replaceState(null, "", `#${tabName}`);
    }

    document.querySelectorAll(".tab-content").forEach((panel) => {
        panel.classList.toggle("active", panel.id === tabName);
    });

    document.querySelectorAll("[data-tab]").forEach((button) => {
        button.classList.toggle("active", button.dataset.tab === tabName);
    });

    if (tabName === "heatmap" && state.pendingRegions) {
        setTimeout(() => {
            _syncMap(state.pendingRegions);
        }, 120);
    }
}

function bindModal() {
    const modalOverlay = document.getElementById("modalOverlay");
    const closeButton = document.getElementById("closeModalBtn");

    document.querySelectorAll("[data-modal-target]").forEach((button) => {
        button.addEventListener("click", () => openModal(button.dataset.modalTarget));
    });

    closeButton.addEventListener("click", closeModal);

    modalOverlay.addEventListener("click", (event) => {
        if (event.target === modalOverlay) {
            closeModal();
        }
    });
}

function openModal(modalName) {
    const config = modalConfig[modalName];
    if (!config) {
        return;
    }

    state.activeModal = modalName;
    document.getElementById("modalTitle").textContent = config.title;
    document.getElementById("modalSubtitle").textContent = config.subtitle;
    document.getElementById("modalOverlay").classList.remove("hidden");

    document.querySelectorAll(".modal-form").forEach((form) => {
        form.classList.add("hidden");
    });

    const form = document.getElementById(config.formId);
    form.classList.remove("hidden");
}

function closeModal() {
    state.activeModal = null;
    document.getElementById("modalOverlay").classList.add("hidden");
}

function bindForms() {
    document.querySelectorAll(".modal-form").forEach((form) => {
        form.addEventListener("submit", async (event) => {
            event.preventDefault();
            await submitForm(form);
        });
    });
}

async function submitForm(form) {
    const submitButton = form.querySelector("button[type='submit']");
    const payload = Object.fromEntries(new FormData(form).entries());
    const originalLabel = submitButton.textContent;

    submitButton.disabled = true;
    submitButton.textContent = "Saving...";

    try {
        const response = await fetch(form.dataset.endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.error || "Unable to save update.");
        }

        state.dashboard = result.dashboard;
        renderDashboard(result.dashboard);
        form.reset();
        closeModal();
        showFlash(result.message, "success");
    } catch (error) {
        showFlash(error.message, "error");
    } finally {
        submitButton.disabled = false;
        submitButton.textContent = originalLabel;
    }
}

async function loadDashboard() {
    try {
        const response = await fetch("/api/dashboard");
        const dashboard = await response.json();
        state.dashboard = dashboard;
        renderDashboard(dashboard);
    } catch (error) {
        showFlash("Unable to load dashboard data.", "error");
    }
}

function renderDashboard(dashboard) {
    renderStatus(dashboard.summary);
    renderSources(dashboard.summary, dashboard.sources);
    renderHeatmap(dashboard.regions);
    renderAllocations(dashboard.allocations);
    renderImpact(dashboard.impact_metrics);
    renderBenefits(dashboard.benefits);
    renderActivity(dashboard.activities);
    populateRegionSelects(dashboard.regions);
}

function renderStatus(summary) {
    const statusEntries = [
        ["Storage backend", summary.storage_backend],
        ["Data sources connected", summary.data_sources_connected],
        ["Records consolidated", formatNumber(summary.records_consolidated)],
        ["Districts mapped", summary.districts_mapped],
        ["Total needs", formatNumber(summary.total_needs)],
        ["Volunteers", formatNumber(summary.volunteers)],
        ["Current coverage", `${summary.current_coverage}%`],
        ["Reports today", summary.reports_today],
        ["Donations today", summary.donations_today],
        ["Funds committed", `INR ${formatNumber(summary.funds_committed)}`],
        ["Resource units", formatNumber(summary.resource_units)],
        ["Volunteers deployed today", formatNumber(summary.deployed_today)],
    ];

    document.getElementById("statusList").innerHTML = statusEntries
        .map(
            ([label, value]) => `
                <div class="stat-row">
                    <span class="stat-label">${escapeHtml(String(label))}</span>
                    <span class="stat-value">${escapeHtml(String(value))}</span>
                </div>
            `
        )
        .join("");
}

function renderSources(summary, sources) {
    const grid = document.getElementById("sourceGrid");
    grid.innerHTML = sources
        .map(
            (source) => `
                <div class="data-source">
                    <div class="data-source-label">${escapeHtml(source.name)}</div>
                    <div class="data-source-desc">${escapeHtml(source.description)}</div>
                    <div class="data-source-count">${formatNumber(source.records)} records</div>
                </div>
            `
        )
        .join("");

    document.getElementById("recordsSummary").innerHTML = `
        <strong>Total data consolidated:</strong> ${formatNumber(summary.records_consolidated)} records from ${summary.data_sources_connected} connected sources.
    `;
}

function renderHeatmap(regions) {
    state.pendingRegions = regions;

    const container = document.getElementById("heatmapGrid");
    container.className = "india-map-container";

    const heatmapTab = document.getElementById("heatmap");
    if (heatmapTab && heatmapTab.classList.contains("active")) {
        _syncMap(regions);
    }

    const topThree = regions.slice(0, 3).map((region) => region.name).join(", ");
    document.getElementById("heatmapInsights").innerHTML = `
        <strong>Instant insight:</strong> the hottest districts right now are ${escapeHtml(topThree)}. These should stay at the front of the next deployment cycle.
    `;
}

function _syncMap(regions) {
    if (typeof initIndiaMap === "undefined") return;
    if (!state.mapReady) {
        initIndiaMap("heatmapGrid", regions);
        state.mapReady = true;
    } else {
        refreshMapMarkers(regions);
    }
}

function renderAllocations(regions) {
    const body = document.getElementById("allocationTableBody");
    body.innerHTML = regions
        .map((region) => {
            const actionTone = toneForRecommendation(region.recommended_deploy);
            return `
                <tr>
                    <td><strong>${escapeHtml(region.name)}</strong><br><span class="region-needs">${escapeHtml(region.focus)}</span></td>
                    <td class="${severityClass(region.severity)}">${formatNumber(region.needs)}</td>
                    <td>${formatNumber(region.volunteers)}</td>
                    <td>${formatNumber(region.deficit)}</td>
                    <td class="action-${actionTone}">${escapeHtml(region.action_label)}</td>
                </tr>
            `;
        })
        .join("");

    const priorityList = regions
        .filter((region) => region.recommended_deploy > 0)
        .slice(0, 3)
        .map((region) => `${region.name} (${region.recommended_deploy})`)
        .join(", ");

    document.getElementById("allocationRecommendation").innerHTML = `
        <strong>Recommended sequence:</strong> ${escapeHtml(priorityList || "Current allocations look stable across all tracked districts.")}.
    `;
}

function renderImpact(metrics) {
    const body = document.getElementById("impactTableBody");
    body.innerHTML = metrics
        .map(
            (metric) => `
                <tr>
                    <td><strong>${escapeHtml(metric.metric)}</strong></td>
                    <td>${escapeHtml(metric.before)}</td>
                    <td>${escapeHtml(metric.after)}</td>
                    <td class="severity-text-low">${escapeHtml(metric.improvement)}</td>
                </tr>
            `
        )
        .join("");
}

function renderBenefits(benefits) {
    const container = document.getElementById("benefitsList");
    container.innerHTML = benefits
        .map(
            (benefit) => `
                <div class="benefit-card">
                    <div class="benefit-title">${escapeHtml(benefit.title)}</div>
                    <div class="benefit-text">${escapeHtml(benefit.description)}</div>
                </div>
            `
        )
        .join("");
}

function renderActivity(activities) {
    const container = document.getElementById("activityFeed");
    if (!activities.length) {
        container.innerHTML = '<div class="empty-state">No activity logged yet.</div>';
        return;
    }

    container.innerHTML = activities
        .map(
            (activity) => `
                <div class="activity-item">
                    <div class="activity-type">${escapeHtml(activity.type)}</div>
                    <div class="activity-title">${escapeHtml(activity.title)}</div>
                    <div class="activity-detail">${escapeHtml(activity.detail)}</div>
                    <div class="activity-time">${escapeHtml(activity.display_time)}</div>
                </div>
            `
        )
        .join("");
}

function populateRegionSelects(regions) {
    const options = regions
        .map((region) => `<option value="${escapeHtml(region.name)}">${escapeHtml(region.name)}</option>`)
        .join("");

    document.querySelectorAll(".region-select").forEach((select) => {
        const currentValue = select.value;
        select.innerHTML = options;
        if (currentValue && [...select.options].some((option) => option.value === currentValue)) {
            select.value = currentValue;
        }
    });
}

function showFlash(message, tone) {
    const flash = document.getElementById("flashMessage");
    flash.textContent = message;
    flash.classList.remove("hidden", "success", "error");
    flash.classList.add(tone);

    window.clearTimeout(showFlash.timeoutId);
    showFlash.timeoutId = window.setTimeout(() => {
        flash.classList.add("hidden");
    }, 3500);
}

function toneForRecommendation(recommendedDeploy) {
    if (recommendedDeploy >= 70) {
        return "critical";
    }
    if (recommendedDeploy >= 35) {
        return "high";
    }
    if (recommendedDeploy > 0) {
        return "medium";
    }
    return "low";
}

function severityClass(severity) {
    return `severity-text-${severity}`;
}

function formatNumber(value) {
    return new Intl.NumberFormat("en-IN").format(Number(value || 0));
}

function escapeHtml(value) {
    return value
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}
