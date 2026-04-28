/**
 * Google Places Autocomplete for LocalPlace admin.
 * Requests all available place fields and auto-fills the admin form.
 */
window.addEventListener("load", function () {
    var addressInput = document.getElementById("id_address");
    if (!addressInput) return;

    // Prevent browser autocomplete from competing
    addressInput.setAttribute("autocomplete", "new-password");

    // Poll until Google Maps Places is available (loaded async)
    var attempts = 0;
    var interval = setInterval(function () {
        attempts++;
        if (typeof google !== "undefined" && google.maps && google.maps.places) {
            clearInterval(interval);
            attachAutocomplete(addressInput);
        }
        if (attempts > 100) clearInterval(interval); // give up after 10s
    }, 100);
});

function attachAutocomplete(input) {
    var autocomplete = new google.maps.places.Autocomplete(input, {
        types: ["geocode", "establishment"],
        // Request every available field so we can fill all admin inputs
        fields: [
            "place_id",
            "formatted_address",
            "geometry",
            "url",
            "website",
            "formatted_phone_number",
            "international_phone_number",
            "rating",
            "user_ratings_total",
            "opening_hours",
            "address_components",
            "types",
            "business_status",
        ],
    });

    // Prevent Enter from submitting the form while dropdown is open
    input.addEventListener("keydown", function (e) {
        if (e.key === "Enter") e.preventDefault();
    });

    autocomplete.addListener("place_changed", function () {
        var nameField = document.getElementById("id_name");
        var originalName = nameField ? nameField.value : "";

        var place = autocomplete.getPlace();
        if (!place || !place.geometry) return;

        // ── Address ───────────────────────────────────────────────────────
        if (place.formatted_address) {
            input.value = place.formatted_address;
        }

        // ── Coordinates ───────────────────────────────────────────────────
        setField("id_latitude", parseFloat(place.geometry.location.lat().toFixed(7)));
        setField("id_longitude", parseFloat(place.geometry.location.lng().toFixed(7)));

        // ── Google Places meta ────────────────────────────────────────────
        setField("id_google_places_id", place.place_id || "");
        setField("id_google_places_link", place.url || "");

        // ── Business details ──────────────────────────────────────────────
        // if (place.name) setField("id_name", place.name);
        if (place.website) setField("id_website_url", place.website);
        if (place.formatted_phone_number) {
            setField("id_contact_number", place.formatted_phone_number);
        } else if (place.international_phone_number) {
            setField("id_contact_number", place.international_phone_number);
        }

        // ── Ratings ───────────────────────────────────────────────────────
        if (place.rating !== undefined) {
            setField("id_popularity_score", place.rating);
        }
        if (place.user_ratings_total !== undefined) {
            setField("id_review_count", place.user_ratings_total);
        }

        // Aggressively restore the original name for 500ms to beat any delayed browser autofill
        if (nameField && originalName) {
            var counter = 0;
            var restoreInterval = setInterval(function () {
                if (nameField.value !== originalName) {
                    console.log("[Places] Overwriting detected! Restoring:", originalName);
                    nameField.value = originalName;
                }
                counter++;
                if (counter > 50) clearInterval(restoreInterval); // Stop after 500ms (10ms * 50)
            }, 10);
        }

        console.log("[Places] Filled fields from:", place.name, place);
    });
}

/** Helper: set value on a form field if it exists and fire change events. */
function setField(id, value) {
    if (id === "id_name") {
        console.log("[Places] Skipping id_name to prevent overwrite.");
        return;
    }

    var el = document.getElementById(id);
    if (el && value !== undefined && value !== null) {
        console.log("[Places] Setting field:", id, "to:", value);
        el.value = value;
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
    }
}

// ─── Image size validation ────────────────────────────────────────────────────
(function () {
    var MAX_MB = 5;
    var MAX_BYTES = MAX_MB * 1024 * 1024;

    // ── Inject shared styles once ─────────────────────────────────────────
    (function injectStyles() {
        if (document.getElementById("lp-upload-styles")) return;
        var style = document.createElement("style");
        style.id = "lp-upload-styles";
        style.textContent = "\n" +
            /* ── Inline error banner ── */
            ".lp-img-error-banner {\n" +
            "  display: flex;\n" +
            "  align-items: flex-start;\n" +
            "  gap: 8px;\n" +
            "  margin: 8px 0 4px;\n" +
            "  padding: 10px 14px;\n" +
            "  background: #fef2f2;\n" +
            "  border: 1.5px solid #fca5a5;\n" +
            "  border-left: 4px solid #ef4444;\n" +
            "  border-radius: 6px;\n" +
            "  font-size: 12px;\n" +
            "  font-weight: 600;\n" +
            "  color: #b91c1c;\n" +
            "  line-height: 1.5;\n" +
            "  animation: lp-shake 0.35s ease;\n" +
            "}\n" +
            ".lp-img-error-banner .lp-err-icon {\n" +
            "  font-size: 15px;\n" +
            "  flex-shrink: 0;\n" +
            "  margin-top: 1px;\n" +
            "}\n" +
            /* ── Toast (info + error) ── */
            "#lp-toast {\n" +
            "  position: fixed;\n" +
            "  bottom: 28px;\n" +
            "  right: 28px;\n" +
            "  z-index: 99999;\n" +
            "  display: flex;\n" +
            "  align-items: flex-start;\n" +
            "  gap: 10px;\n" +
            "  min-width: 290px;\n" +
            "  max-width: 370px;\n" +
            "  padding: 14px 16px;\n" +
            "  border-radius: 10px;\n" +
            "  box-shadow: 0 8px 32px rgba(0,0,0,0.22);\n" +
            "  font-family: inherit;\n" +
            "  font-size: 13px;\n" +
            "  font-weight: 500;\n" +
            "  line-height: 1.5;\n" +
            "  opacity: 0;\n" +
            "  transform: translateY(16px);\n" +
            "  transition: opacity 0.28s ease, transform 0.28s ease;\n" +
            "  pointer-events: none;\n" +
            "}\n" +
            "#lp-toast.lp-toast-visible {\n" +
            "  opacity: 1;\n" +
            "  transform: translateY(0);\n" +
            "  pointer-events: auto;\n" +
            "}\n" +
            "#lp-toast.lp-toast-info {\n" +
            "  background: #1e40af;\n" +
            "  color: #fff;\n" +
            "  border: 1.5px solid #3b82f6;\n" +
            "}\n" +
            "#lp-toast.lp-toast-error {\n" +
            "  background: #7f1d1d;\n" +
            "  color: #fff;\n" +
            "  border: 1.5px solid #ef4444;\n" +
            "}\n" +
            "#lp-toast .lp-toast-icon { font-size: 20px; flex-shrink: 0; line-height: 1; }\n" +
            "#lp-toast .lp-toast-body { flex: 1; }\n" +
            "#lp-toast .lp-toast-title { font-weight: 700; font-size: 13px; margin-bottom: 3px; }\n" +
            "#lp-toast .lp-toast-msg  { font-size: 12px; opacity: 0.9; }\n" +
            /* ── Shake keyframe ── */
            "@keyframes lp-shake {\n" +
            "  0%,100% { transform: translateX(0); }\n" +
            "  20%     { transform: translateX(-5px); }\n" +
            "  40%     { transform: translateX(5px); }\n" +
            "  60%     { transform: translateX(-4px); }\n" +
            "  80%     { transform: translateX(4px); }\n" +
            "}\n";
        document.head.appendChild(style);
    })();

    // ── Toast helper ──────────────────────────────────────────────────────
    var toastTimer = null;

    function showToast(type, title, msg, duration) {
        duration = duration || 3500;
        var el = document.getElementById("lp-toast");
        if (!el) {
            el = document.createElement("div");
            el.id = "lp-toast";
            el.innerHTML =
                '<span class="lp-toast-icon"></span>' +
                '<div class="lp-toast-body">' +
                '<div class="lp-toast-title"></div>' +
                '<div class="lp-toast-msg"></div>' +
                '</div>';
            document.body.appendChild(el);
        }

        // Reset class, then set type class
        el.className = "lp-toast-" + type;
        el.querySelector(".lp-toast-icon").textContent = type === "info" ? "\u2139\ufe0f" : "\uD83D\uDEAB";
        el.querySelector(".lp-toast-title").textContent = title;
        el.querySelector(".lp-toast-msg").textContent = msg;

        // Replay transition even if already visible
        el.classList.remove("lp-toast-visible");
        void el.offsetWidth;
        el.classList.add("lp-toast-visible");

        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () {
            el.classList.remove("lp-toast-visible");
        }, duration);
    }

    // ── Inline error banner ───────────────────────────────────────────────
    function setError(input, message) {
        var cell = input.closest("td") || input.parentNode;
        var banner = cell.querySelector(".lp-img-error-banner");

        if (message) {
            if (!banner) {
                banner = document.createElement("div");
                banner.className = "lp-img-error-banner";
                banner.innerHTML =
                    '<span class="lp-err-icon">\uD83D\uDEAB</span>' +
                    '<span class="lp-err-text"></span>';
                cell.appendChild(banner);
            }
            // Re-trigger shake animation
            banner.style.animation = "none";
            void banner.offsetWidth;
            banner.style.animation = "";

            banner.querySelector(".lp-err-text").textContent = message;
            banner.style.display = "flex";
            input.style.outline = "2px solid #ef4444";
            input.style.borderRadius = "4px";
        } else {
            if (banner) banner.style.display = "none";
            input.style.outline = "";
            input.style.borderRadius = "";
        }
    }

    // ── Wire up a single file input ───────────────────────────────────────
    function attachValidation(input) {
        if (input.dataset.sizeValidationAttached) return;
        input.dataset.sizeValidationAttached = "1";

        // Click → info toast reminding user of the limit
        input.addEventListener("click", function () {
            showToast(
                "info",
                "Image upload limit",
                "Please upload images up to " + MAX_MB + " MB only. Larger files will be rejected.",
                4000
            );
        });

        // Change → validate immediately and show error if needed
        input.addEventListener("change", function () {
            var file = this.files && this.files[0];
            if (!file) { setError(this, null); return; }

            if (file.size > MAX_BYTES) {
                var sizeMB = (file.size / (1024 * 1024)).toFixed(1);
                var msg = "File too large: " + sizeMB + " MB \u2014 maximum allowed is " + MAX_MB + " MB.";
                setError(this, msg);
                showToast("error", "File too large", msg, 5000);
                this.value = ""; // clear the bad selection
            } else {
                setError(this, null);
            }
        });
    }

    // ── Block submit if any file is oversized (safety net) ────────────────
    function blockSubmitIfErrors(form) {
        if (form.dataset.sizeSubmitBlocked) return;
        form.dataset.sizeSubmitBlocked = "1";

        form.addEventListener("submit", function (e) {
            var inputs = form.querySelectorAll("input[type='file']");
            var hasError = false;

            inputs.forEach(function (input) {
                var file = input.files && input.files[0];
                if (file && file.size > MAX_BYTES) {
                    var sizeMB = (file.size / (1024 * 1024)).toFixed(1);
                    setError(
                        input,
                        "File too large: " + sizeMB + " MB \u2014 maximum allowed is " + MAX_MB + " MB."
                    );
                    hasError = true;
                }
            });

            if (hasError) {
                e.preventDefault();
                e.stopImmediatePropagation();
                showToast(
                    "error",
                    "Cannot save \u2014 oversized file",
                    "One or more images exceed " + MAX_MB + " MB. Remove them and try again.",
                    6000
                );
                window.scrollTo({ top: 0, behavior: "smooth" });
            }
        });
    }

    // ── Scan all inputs (handles dynamic inline rows too) ─────────────────
    function scanAndAttach() {
        document.querySelectorAll("input[type='file']").forEach(attachValidation);
        var form = document.querySelector("form#localplace_form, form");
        if (form) blockSubmitIfErrors(form);
    }

    window.addEventListener("load", function () {
        scanAndAttach();
        // MutationObserver catches "Add another image" inline rows
        var observer = new MutationObserver(scanAndAttach);
        observer.observe(document.body, { childList: true, subtree: true });
    });
})();
