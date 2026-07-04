// ─── Sticky navbar shadow on scroll ──────────────────────
document.addEventListener("DOMContentLoaded", function () {
    const navbar = document.querySelector(".navbar");
    if (navbar) {
        window.addEventListener("scroll", function () {
            if (window.scrollY > 10) {
                navbar.classList.add("scrolled");
            } else {
                navbar.classList.remove("scrolled");
            }
        });
    }
});

// ─── Inline form validation (replaces alert()) ────────────
function showInlineError(inputEl, message) {
    // Remove any existing error
    clearInlineError(inputEl);

    inputEl.classList.add("is-invalid");
    const feedback = document.createElement("div");
    feedback.className = "invalid-feedback";
    feedback.textContent = message;
    inputEl.parentNode.appendChild(feedback);
}

function clearInlineError(inputEl) {
    inputEl.classList.remove("is-invalid");
    const existing = inputEl.parentNode.querySelector(".invalid-feedback");
    if (existing) existing.remove();
}

// Profile form validation
const form = document.getElementById("profileForm");

if (form) {
    const fullnameInput = document.getElementById("fullname");
    const phoneInput = document.getElementById("phone");

    form.addEventListener("submit", function (e) {
        let valid = true;

        const name = fullnameInput ? fullnameInput.value.trim() : "";
        const phone = phoneInput ? phoneInput.value.trim() : "";

        if (fullnameInput) clearInlineError(fullnameInput);
        if (phoneInput) clearInlineError(phoneInput);

        if (name.length < 3) {
            showInlineError(fullnameInput, "Name must be at least 3 characters.");
            valid = false;
        }

        const phoneRegex = /^[0-9]{10}$/;
        if (phone !== "" && !phoneRegex.test(phone)) {
            showInlineError(phoneInput, "Enter a valid 10-digit phone number.");
            valid = false;
        }

        if (!valid) e.preventDefault();
    });

    // Clear error on input
    if (fullnameInput) fullnameInput.addEventListener("input", () => clearInlineError(fullnameInput));
    if (phoneInput) phoneInput.addEventListener("input", () => clearInlineError(phoneInput));
}

// ─── Resume file validation ───────────────────────────────
const resumeInput = document.getElementById("resume");

if (resumeInput) {
    resumeInput.addEventListener("change", function () {
        const file = this.files[0];
        if (!file) return;

        const allowed = [
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ];

        if (!allowed.includes(file.type)) {
            showInlineError(this, "Only PDF, DOC or DOCX files are allowed.");
            this.value = "";
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            showInlineError(this, "Maximum file size is 5MB.");
            this.value = "";
            return;
        }

        clearInlineError(this);
    });
}

// ─── Password show / hide toggle ─────────────────────────
document.querySelectorAll(".password-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
        const wrapper = this.closest(".password-wrapper");
        const input = wrapper ? wrapper.querySelector("input") : null;
        if (!input) return;

        const isPassword = input.type === "password";
        input.type = isPassword ? "text" : "password";
        this.innerHTML = isPassword
            ? '<i class="fa fa-eye-slash"></i>'
            : '<i class="fa fa-eye"></i>';
    });
});
