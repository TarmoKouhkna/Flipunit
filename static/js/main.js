// Mobile menu toggle
document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (mobileMenuToggle && navMenu) {
        mobileMenuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!navMenu.contains(event.target) && !mobileMenuToggle.contains(event.target)) {
                navMenu.classList.remove('active');
            }
        });
    }

    // File upload drag and drop
    const fileUploadAreas = document.querySelectorAll('.file-upload-area');
    fileUploadAreas.forEach(area => {
        const input = area.querySelector('input[type="file"]');
        if (!input) return;

        area.addEventListener('dragover', function(e) {
            e.preventDefault();
            area.classList.add('dragover');
        });

        area.addEventListener('dragleave', function() {
            area.classList.remove('dragover');
        });

        area.addEventListener('drop', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                input.files = e.dataTransfer.files;
                // Trigger change event
                const event = new Event('change', { bubbles: true });
                input.dispatchEvent(event);
            }
        });

        area.addEventListener('click', function() {
            input.click();
        });
    });
});

