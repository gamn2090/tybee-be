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

    /** Show or clear a red error message inside the file input's table cell. */
    function setError(input, message) {
        var cell = input.closest("td") || input.parentNode;
        var errEl = cell.querySelector(".localplace-img-error");
        if (!errEl) {
            errEl = document.createElement("p");
            errEl.className = "localplace-img-error";
            errEl.style.cssText = [
                "margin: 4px 0 0 0",
                "font-size: 11px",
                "font-weight: 600",
                "color: #ef4444",
                "line-height: 1.4",
            ].join(";");
            cell.appendChild(errEl);
        }

        if (message) {
            errEl.textContent = "\u274c " + message;
            errEl.style.display = "block";
            input.style.outline = "2px solid #ef4444";
        } else {
            errEl.style.display = "none";
            input.style.outline = "";
        }
    }

    /** Attach change listener to validate file size on selection. */
    function attachValidation(input) {
        if (input.dataset.sizeValidationAttached) return;
        input.dataset.sizeValidationAttached = "1";

        input.addEventListener("change", function () {
            var file = this.files && this.files[0];
            if (!file) {
                setError(this, null);
                return;
            }

            if (file.size > MAX_BYTES) {
                var sizeMB = (file.size / (1024 * 1024)).toFixed(1);
                setError(
                    this,
                    "File too large: " + sizeMB + " MB. Maximum allowed is " + MAX_MB + " MB."
                );
                this.value = ""; // Clear the selection
            } else {
                setError(this, null);
            }
        });
    }

    /** Block form submission if any file input still has an oversized file. */
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
                        "File too large: " + sizeMB + " MB. Maximum allowed is " + MAX_MB + " MB."
                    );
                    hasError = true;
                }
            });

            if (hasError) {
                e.preventDefault();
                e.stopImmediatePropagation();
                window.scrollTo({ top: 0, behavior: "smooth" });
                alert(
                    "One or more images exceed the " + MAX_MB +
                    " MB size limit. Please remove them before saving."
                );
            }
        });
    }

    /** Scan for all file inputs and wire them up. Also handles dynamically added inline rows. */
    function scanAndAttach() {
        document.querySelectorAll("input[type='file']").forEach(function (input) {
            attachValidation(input);
        });

        var form = document.querySelector("form#localplace_form, form");
        if (form) blockSubmitIfErrors(form);
    }

    // Initial scan on page load
    window.addEventListener("load", function () {
        scanAndAttach();

        // Watch for new inline rows added dynamically (e.g. "Add another Local Place Image")
        var observer = new MutationObserver(function () {
            scanAndAttach();
        });
        observer.observe(document.body, { childList: true, subtree: true });
    });
})();
