window.addEventListener("load", function () {
    var typeField = document.getElementById("id_map_file_type");
    if (!typeField) return;

    function toggleSections() {
        var selectedType = typeField.value;
        
        // Find all fieldsets
        var fieldsets = document.querySelectorAll("fieldset");
        
        fieldsets.forEach(function(fs) {
            var h2 = fs.querySelector("h2");
            if (!h2) return;
            
            var title = h2.textContent.trim();
            
            if (title === "Image Upload") {
                fs.style.display = (selectedType === "image") ? "" : "none";
            } else if (title === "PDF Upload") {
                fs.style.display = (selectedType === "pdf") ? "" : "none";
            }
        });

        // Also handle individual fields if they are not in those fieldsets for some reason
        // (though we specifically put them there in admin.py)
    }

    typeField.addEventListener("change", toggleSections);
    toggleSections(); // Initial run
});
