(function () {
    function init() {
        var typeField = document.getElementById("id_map_file_type");
        if (!typeField) {
            console.log("[CartMapAdmin] Map type field not found yet...");
            return;
        }

        console.log("[CartMapAdmin] Initializing visibility toggle.");

        function toggleSections() {
            var selectedType = typeField.value;
            console.log("[CartMapAdmin] Selected map type:", selectedType);

            // We search for the specific fields and then hide their containing "sections"
            // field-image and field-pdf are standard Django classes for form rows
            var imgFieldRow = document.querySelector(".field-image, .field-image_preview, #id_image");
            var pdfFieldRow = document.querySelector(".field-pdf, .field-pdf_preview, #id_pdf");

            if (imgFieldRow) {
                // In Unfold/Django, fields are usually inside a fieldset or a section div
                var container = imgFieldRow.closest("fieldset") || imgFieldRow.closest(".module") || imgFieldRow.closest("section");
                if (container) {
                    container.style.display = (selectedType === "image") ? "" : "none";
                    console.log("[CartMapAdmin] Image container toggled:", container);
                }
            }

            if (pdfFieldRow) {
                var container = pdfFieldRow.closest("fieldset") || pdfFieldRow.closest(".module") || pdfFieldRow.closest("section");
                if (container) {
                    container.style.display = (selectedType === "pdf") ? "" : "none";
                    console.log("[CartMapAdmin] PDF container toggled:", container);
                }
            }
        }

        typeField.addEventListener("change", toggleSections);

        // Initial run with multiple attempts to handle dynamic theme rendering
        toggleSections();
        setTimeout(toggleSections, 50);
        setTimeout(toggleSections, 250);
        setTimeout(toggleSections, 1000);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
    // Also trigger on window load as a fallback
    window.addEventListener("load", init);
})();
