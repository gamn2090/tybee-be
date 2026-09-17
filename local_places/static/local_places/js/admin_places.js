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
        var loc = place.geometry.viewport
            ? place.geometry.viewport.getCenter()
            : place.geometry.location;

        setField("id_latitude", parseFloat(loc.lat().toFixed(7)));
        setField("id_longitude", parseFloat(loc.lng().toFixed(7)));

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
            "  top: 24px;\n" +
            "  right: 24px;\n" +
            "  z-index: 99999;\n" +
            "  display: flex;\n" +
            "  align-items: flex-start;\n" +
            "  gap: 12px;\n" +
            "  min-width: 320px;\n" +
            "  max-width: 420px;\n" +
            "  padding: 16px 18px;\n" +
            "  border-radius: 12px;\n" +
            "  box-shadow: 0 12px 40px rgba(0,0,0,0.32), 0 2px 8px rgba(0,0,0,0.18);\n" +
            "  font-family: inherit;\n" +
            "  font-size: 14px;\n" +
            "  font-weight: 500;\n" +
            "  line-height: 1.5;\n" +
            "  opacity: 0;\n" +
            "  transform: translateY(-20px);\n" +
            "  transition: opacity 0.3s ease, transform 0.3s ease;\n" +
            "  pointer-events: none;\n" +
            "}\n" +
            "#lp-toast.lp-toast-visible {\n" +
            "  opacity: 1;\n" +
            "  transform: translateY(0);\n" +
            "  pointer-events: auto;\n" +
            "}\n" +
            "#lp-toast.lp-toast-info {\n" +
            "  background: linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 100%);\n" +
            "  color: #fff;\n" +
            "  border: 2px solid #60a5fa;\n" +
            "  border-top: 4px solid #93c5fd;\n" +
            "}\n" +
            "#lp-toast.lp-toast-error {\n" +
            "  background: linear-gradient(135deg, #7f1d1d 0%, #b91c1c 100%);\n" +
            "  color: #fff;\n" +
            "  border: 2px solid #f87171;\n" +
            "  border-top: 4px solid #fca5a5;\n" +
            "}\n" +
            "#lp-toast .lp-toast-icon { font-size: 24px; flex-shrink: 0; line-height: 1; margin-top: 1px; }\n" +
            "#lp-toast .lp-toast-body { flex: 1; }\n" +
            "#lp-toast .lp-toast-title { font-weight: 800; font-size: 14px; margin-bottom: 4px; letter-spacing: 0.01em; }\n" +
            "#lp-toast .lp-toast-msg  { font-size: 13px; opacity: 0.92; }\n" +
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
                5000
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
                showToast("error", "File too large", msg, 6000);
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
                    7000
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

// ─── Search suggestions dropdown (Admin issue #1) ─────────────────────────────
(function () {
    function init() {
        var input = document.getElementById("searchbar");
        if (!input || input.dataset.suggestionsAttached) return;
        input.dataset.suggestionsAttached = "1";

        var suggestUrl = window.location.pathname.replace(/\/?$/, "/") + "search-suggestions/";
        var wrapper = input.closest("#toolbar") || input.parentNode;
        wrapper.style.position = wrapper.style.position || "relative";

        var dropdown = document.createElement("div");
        dropdown.id = "lp-search-suggestions";
        dropdown.style.cssText =
            "display:none;position:absolute;z-index:1000;background:#fff;" +
            "border:1px solid #d1d5db;border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,0.12);" +
            "max-height:260px;overflow-y:auto;min-width:240px;margin-top:4px;";
        wrapper.appendChild(dropdown);

        function positionDropdown() {
            var rect = input.getBoundingClientRect();
            var wrapperRect = wrapper.getBoundingClientRect();
            dropdown.style.left = (rect.left - wrapperRect.left) + "px";
            dropdown.style.top = (rect.bottom - wrapperRect.top) + "px";
            dropdown.style.width = rect.width + "px";
        }

        function hideDropdown() {
            dropdown.style.display = "none";
        }

        function renderResults(results) {
            dropdown.innerHTML = "";
            if (!results.length) {
                hideDropdown();
                return;
            }
            results.forEach(function (item) {
                var row = document.createElement("div");
                row.textContent = item.category ? item.name + "  —  " + item.category : item.name;
                row.style.cssText =
                    "padding:8px 12px;cursor:pointer;font-size:13px;color:#111827;";
                row.addEventListener("mouseenter", function () {
                    row.style.background = "#f3f4f6";
                });
                row.addEventListener("mouseleave", function () {
                    row.style.background = "transparent";
                });
                row.addEventListener("mousedown", function (e) {
                    // mousedown (not click) so it fires before the input's blur
                    e.preventDefault();
                    input.value = item.name;
                    hideDropdown();
                    input.form.submit();
                });
                dropdown.appendChild(row);
            });
            positionDropdown();
            dropdown.style.display = "block";
        }

        var debounceTimer = null;
        var currentController = null;

        input.addEventListener("input", function () {
            var query = input.value.trim();
            clearTimeout(debounceTimer);
            if (!query) {
                hideDropdown();
                return;
            }
            debounceTimer = setTimeout(function () {
                if (currentController) currentController.abort();
                currentController = new AbortController();
                fetch(suggestUrl + "?q=" + encodeURIComponent(query), {
                    signal: currentController.signal,
                    credentials: "same-origin",
                })
                    .then(function (res) {
                        return res.ok ? res.json() : { results: [] };
                    })
                    .then(function (data) {
                        renderResults(data.results || []);
                    })
                    .catch(function () {
                        /* ignore aborted/failed requests */
                    });
            }, 200);
        });

        input.addEventListener("blur", function () {
            // Delay so a mousedown on a suggestion can still register
            setTimeout(hideDropdown, 150);
        });

        window.addEventListener("resize", positionDropdown);
    }

    window.addEventListener("load", init);
})();