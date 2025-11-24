// Mobile menu toggle and navbar functionality
(function() {
    'use strict';
    
    function initNavbar() {
        const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
        const navMenu = document.querySelector('.nav-menu');

        if (!mobileMenuToggle || !navMenu) return;

        // Mobile menu toggle button
        mobileMenuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            navMenu.classList.toggle('active');
        });

        // Ensure all navbar links always work - close mobile menu on click
        const allNavLinks = document.querySelectorAll('.nav-menu a, .navbar a.logo');
        allNavLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                // Close mobile menu if open
                if (navMenu.classList.contains('active')) {
                    navMenu.classList.remove('active');
                }
                // Allow normal navigation - don't prevent default
            }, { passive: true });
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            const clickedNavLink = event.target.closest('.nav-menu a');
            const clickedToggle = event.target.closest('.mobile-menu-toggle');
            const clickedLogo = event.target.closest('.navbar a.logo');
            
            // Don't interfere with navbar links or toggle
            if (clickedNavLink || clickedToggle || clickedLogo) {
                return;
            }
            
            // Close menu if clicking outside
            if (navMenu.classList.contains('active') && 
                !navMenu.contains(event.target) && 
                !mobileMenuToggle.contains(event.target)) {
                navMenu.classList.remove('active');
            }
        });
    }
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNavbar);
    } else {
        initNavbar();
    }
})();

// File upload drag and drop
document.addEventListener('DOMContentLoaded', function() {
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

        area.addEventListener('click', function(e) {
            // Only trigger file input if click is not directly on the input itself
            if (e.target !== input && !input.contains(e.target)) {
                input.click();
            }
        });
    });
});

// Feedback character counter
document.addEventListener('DOMContentLoaded', function() {
    const feedbackTextarea = document.getElementById('feedback-textarea');
    const charCount = document.getElementById('char-count');
    
    if (feedbackTextarea && charCount) {
        // Update counter on input
        feedbackTextarea.addEventListener('input', function() {
            const length = this.value.length;
            charCount.textContent = length;
            
            // Change color when approaching limit
            if (length > 900) {
                charCount.style.color = '#ef4444'; // Red
            } else if (length > 800) {
                charCount.style.color = '#f59e0b'; // Orange
            } else {
                charCount.style.color = '';
            }
        });
        
        // Initialize counter
        charCount.textContent = feedbackTextarea.value.length;
    }
});

