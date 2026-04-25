const CAPTCHA_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789";
const ROLE_PROFILES = {
    admin: {
        username: "ADMIN-SRAS-2026",
        label: "Continue as Admin",
    },
    user: {
        username: "USER-NGO-2026",
        label: "Continue as User",
    },
};

document.addEventListener("DOMContentLoaded", () => {
    bindFontControls();
    bindRoleSelection();
    bindCaptcha();
});

function bindFontControls() {
    const root = document.documentElement;
    let fontScale = 100;

    document.querySelectorAll("[data-font-adjust]").forEach((button) => {
        button.addEventListener("click", () => {
            const delta = Number(button.dataset.fontAdjust || 0);
            fontScale = Math.min(118, Math.max(92, fontScale + delta * 4));
            root.style.fontSize = `${fontScale}%`;
        });
    });
}

function bindRoleSelection() {
    const roleInput = document.getElementById("roleInput");
    const usernameInput = document.getElementById("username");
    const submitButton = document.getElementById("loginSubmitButton");
    const roleButtons = document.querySelectorAll("[data-role-option]");

    if (!roleInput || !usernameInput || !submitButton || !roleButtons.length) {
        return;
    }

    const applyRole = (role) => {
        const safeRole = ROLE_PROFILES[role] ? role : "user";
        roleInput.value = safeRole;
        usernameInput.value = ROLE_PROFILES[safeRole].username;
        submitButton.textContent = ROLE_PROFILES[safeRole].label;

        roleButtons.forEach((button) => {
            button.classList.toggle("active", button.dataset.roleOption === safeRole);
        });
    };

    roleButtons.forEach((button) => {
        button.addEventListener("click", () => applyRole(button.dataset.roleOption));
    });

    applyRole(roleInput.value || "user");
}

function bindCaptcha() {
    const form = document.querySelector("[data-captcha-form]");
    const display = document.getElementById("captchaText");
    const input = document.getElementById("captcha");
    const errorBox = document.getElementById("captchaError");
    const refreshButton = document.getElementById("refreshCaptcha");

    if (!form || !display || !input || !errorBox || !refreshButton) {
        return;
    }

    const refresh = (clearError = true) => {
        display.textContent = createCaptcha();
        input.value = "";
        if (clearError) {
            hideError(errorBox);
        }
    };

    refreshButton.addEventListener("click", refresh);

    form.addEventListener("submit", (event) => {
        const typed = input.value.trim().toUpperCase();
        const expected = display.textContent.trim().toUpperCase();

        if (!typed || typed !== expected) {
            event.preventDefault();
            refresh(false);
            errorBox.textContent = "Captcha did not match. Please try again.";
            errorBox.classList.remove("hidden");
            input.focus();
        }
    });

    refresh();
}

function createCaptcha() {
    let value = "";
    for (let index = 0; index < 5; index += 1) {
        const randomIndex = Math.floor(Math.random() * CAPTCHA_CHARS.length);
        value += CAPTCHA_CHARS.charAt(randomIndex);
    }
    return value;
}

function hideError(errorBox) {
    errorBox.textContent = "";
    errorBox.classList.add("hidden");
}
