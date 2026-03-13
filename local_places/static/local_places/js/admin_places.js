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
            "name",
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
        if (place.name) setField("id_name", place.name);
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

        console.log("[Places] Filled fields from:", place.name, place);
    });
}

/** Helper: set value on a form field if it exists and fire change events. */
function setField(id, value) {
    var el = document.getElementById(id);
    if (el && value !== undefined && value !== null) {
        el.value = value;
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
    }
}
