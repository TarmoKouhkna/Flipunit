/**
 * Hybrid Neumorphism + Glassmorphism Interactions
 * 
 * Handles:
 * - Dark mode toggle with localStorage persistence
 * - Search filtering (client-side category filtering)
 * - Feedback modal (open/close, character counter)
 * - Smooth animations and micro-interactions
 */

(function() {
    'use strict';
    
    // ============================================
    // DARK MODE TOGGLE
    // ============================================
    
    function initDarkMode() {
        const toggle = document.getElementById('dark-mode-toggle-hybrid');
        if (!toggle) return;
        
        // Get saved theme or detect system preference
        const savedTheme = localStorage.getItem('theme');
        const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        
        let currentTheme = savedTheme || (systemPrefersDark ? 'dark' : 'light');
        
        // Apply theme
        function applyTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            
            // Update toggle icon visibility
            const sunIcon = toggle.querySelector('.sun-icon');
            const moonIcon = toggle.querySelector('.moon-icon');
            if (sunIcon && moonIcon) {
                if (theme === 'dark') {
                    sunIcon.style.display = 'none';
                    moonIcon.style.display = 'block';
                } else {
                    sunIcon.style.display = 'block';
                    moonIcon.style.display = 'none';
                }
            }
        }
        
        // Initialize theme
        applyTheme(currentTheme);
        
        // Listen for system preference changes (if no saved preference)
        if (!savedTheme) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
                if (!localStorage.getItem('theme')) {
                    applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
        
        // Toggle on click
        toggle.addEventListener('click', function() {
            currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(currentTheme);
        });
    }
    
    // ============================================
    // SEARCH FILTERING (Client-side category filtering)
    // ============================================
    
    function initSearchFilter() {
        const searchInput = document.getElementById('hybrid-search-input');
        const categoryCards = document.querySelectorAll('.hybrid-category-card');
        
        if (!searchInput || categoryCards.length === 0) return;
        
        function filterCategories(query) {
            const searchTerm = query.toLowerCase().trim();
            let visibleCount = 0;
            
            categoryCards.forEach(function(card) {
                const title = card.querySelector('h3')?.textContent.toLowerCase() || '';
                const description = card.querySelector('p')?.textContent.toLowerCase() || '';
                const matches = !searchTerm || title.includes(searchTerm) || description.includes(searchTerm);
                
                if (matches) {
                    card.style.display = 'flex';
                    visibleCount++;
                    // Add fade-in animation
                    card.style.opacity = '0';
                    setTimeout(function() {
                        card.style.transition = 'opacity 0.2s ease';
                        card.style.opacity = '1';
                    }, 10);
                } else {
                    card.style.display = 'none';
                }
            });
            
            // Show "no results" message if needed
            let noResultsMsg = document.getElementById('no-results-message');
            if (visibleCount === 0 && searchTerm) {
                if (!noResultsMsg) {
                    noResultsMsg = document.createElement('p');
                    noResultsMsg.id = 'no-results-message';
                    noResultsMsg.className = 'hybrid-no-results';
                    noResultsMsg.textContent = 'No categories found matching your search.';
                    noResultsMsg.style.textAlign = 'center';
                    noResultsMsg.style.color = 'var(--text-secondary)';
                    noResultsMsg.style.marginTop = 'var(--space-lg)';
                    document.querySelector('.hybrid-categories-grid')?.parentElement.appendChild(noResultsMsg);
                }
                noResultsMsg.style.display = 'block';
            } else if (noResultsMsg) {
                noResultsMsg.style.display = 'none';
            }
        }
        
        // Filter on input
        searchInput.addEventListener('input', function(e) {
            filterCategories(e.target.value);
        });
        
        // Filter on page load if there's a query parameter
        const urlParams = new URLSearchParams(window.location.search);
        const initialQuery = urlParams.get('q');
        if (initialQuery) {
            searchInput.value = initialQuery;
            filterCategories(initialQuery);
        }
    }
    
    // ============================================
    // FEEDBACK MODAL
    // ============================================
    
    function initFeedbackModal() {
        const feedbackBtn = document.getElementById('hybrid-feedback-btn');
        const modalOverlay = document.getElementById('hybrid-modal-overlay');
        const modalClose = document.getElementById('hybrid-modal-close');
        const feedbackForm = document.getElementById('hybrid-feedback-form');
        const feedbackTextarea = document.getElementById('hybrid-feedback-textarea');
        const charCount = document.getElementById('hybrid-char-count');
        const maxLength = 1000;
        
        if (!feedbackBtn || !modalOverlay) return;
        
        // Open modal
        function openModal() {
            modalOverlay.classList.add('active');
            document.body.style.overflow = 'hidden';
            // Focus textarea
            if (feedbackTextarea) {
                setTimeout(function() {
                    feedbackTextarea.focus();
                }, 100);
            }
        }
        
        // Close modal
        function closeModal() {
            modalOverlay.classList.remove('active');
            document.body.style.overflow = '';
            // Clear form if needed
            if (feedbackForm && !feedbackForm.dataset.submitted) {
                feedbackForm.reset();
                updateCharCount();
            }
        }
        
        // Update character count
        function updateCharCount() {
            if (!charCount || !feedbackTextarea) return;
            
            const currentLength = feedbackTextarea.value.length;
            const remaining = maxLength - currentLength;
            
            charCount.textContent = currentLength + '/' + maxLength;
            
            // Update styling based on remaining characters
            charCount.classList.remove('warning', 'error');
            if (remaining < 50) {
                charCount.classList.add('error');
            } else if (remaining < 100) {
                charCount.classList.add('warning');
            }
        }
        
        // Event listeners
        feedbackBtn.addEventListener('click', openModal);
        
        if (modalClose) {
            modalClose.addEventListener('click', closeModal);
        }
        
        // Close on overlay click
        modalOverlay.addEventListener('click', function(e) {
            if (e.target === modalOverlay) {
                closeModal();
            }
        });
        
        // Close on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && modalOverlay.classList.contains('active')) {
                closeModal();
            }
        });
        
        // Character counter
        if (feedbackTextarea && charCount) {
            feedbackTextarea.addEventListener('input', updateCharCount);
            updateCharCount(); // Initial count
            
            // Prevent exceeding max length
            feedbackTextarea.addEventListener('input', function(e) {
                if (e.target.value.length > maxLength) {
                    e.target.value = e.target.value.substring(0, maxLength);
                    updateCharCount();
                }
            });
        }
        
        // Handle form submission
        if (feedbackForm) {
            feedbackForm.addEventListener('submit', function(e) {
                const textarea = this.querySelector('textarea');
                if (textarea && textarea.value.trim().length === 0) {
                    e.preventDefault();
                    alert('Please enter your feedback before submitting.');
                    textarea.focus();
                    return false;
                }
                
                // Mark as submitted to prevent clearing
                this.dataset.submitted = 'true';
                
                // Show loading state
                const submitBtn = this.querySelector('.hybrid-feedback-submit');
                if (submitBtn) {
                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Sending...';
                }
            });
        }
    }
    
    // ============================================
    // MOBILE MENU TOGGLE - REMOVED (using inline nav)
    // ============================================
    
    function initMobileMenu() {
        // No longer needed - using inline navigation menu
        return;
    }
    
    // ============================================
    // SMOOTH SCROLL & MICRO-INTERACTIONS
    // ============================================
    
    function initSmoothInteractions() {
        // Add subtle hover effects to category cards
        const categoryCards = document.querySelectorAll('.hybrid-category-card');
        categoryCards.forEach(function(card) {
            card.addEventListener('mouseenter', function() {
                this.style.transition = 'transform 0.2s ease, box-shadow 0.2s ease';
            });
        });
        
        // Lazy load images (if needed)
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver(function(entries, observer) {
                entries.forEach(function(entry) {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        if (img.dataset.src) {
                            img.src = img.dataset.src;
                            img.removeAttribute('data-src');
                            observer.unobserve(img);
                        }
                    }
                });
            });
            
            document.querySelectorAll('img[data-src]').forEach(function(img) {
                imageObserver.observe(img);
            });
        }
    }
    
    // ============================================
    // LOGO TEXT VISIBILITY
    // ============================================
    
    function initLogoText() {
        const logoImg = document.querySelector('.hybrid-logo-img');
        const logoText = document.querySelector('.hybrid-logo-text');
        
        if (!logoImg || !logoText) return;
        
        // Show text if image fails to load
        logoImg.addEventListener('error', function() {
            this.style.display = 'none';
            if (logoText) {
                logoText.style.display = 'inline-block';
            }
        });
        
        // Keep text visible - don't hide it when image loads
        // Logo text should always be visible
        
        // Check if image failed to load
        if (logoImg.complete && logoImg.naturalHeight === 0) {
            // Image failed to load
            logoImg.style.display = 'none';
            logoText.style.display = 'inline-block';
        }
    }
    
    // ============================================
    // NUMBER INPUT SPINNER BUTTONS
    // ============================================
    
    function initNumberInputSpinners() {
        const numberInputs = document.querySelectorAll('input[type="number"].form-control');
        
        numberInputs.forEach(function(input) {
            // Skip if already has spinner buttons
            if (input.parentElement.classList.contains('number-input-wrapper')) {
                return;
            }
            
            // Skip the amount input in currency converter (no spinners needed)
            if (input.id === 'amount' && input.closest('#converter-form')) {
                return;
            }
            
            // Create wrapper
            const wrapper = document.createElement('div');
            wrapper.className = 'number-input-wrapper';
            
            // Insert wrapper before input
            input.parentNode.insertBefore(wrapper, input);
            
            // Move input into wrapper
            wrapper.appendChild(input);
            
            // Create spinner buttons container
            const spinnerContainer = document.createElement('div');
            spinnerContainer.className = 'number-spinner-buttons';
            
            // Create up button
            const upBtn = document.createElement('button');
            upBtn.type = 'button';
            upBtn.className = 'number-spinner-btn number-spinner-btn-up';
            upBtn.setAttribute('aria-label', 'Increment');
            upBtn.setAttribute('tabindex', '-1');
            
            // Create down button
            const downBtn = document.createElement('button');
            downBtn.type = 'button';
            downBtn.className = 'number-spinner-btn number-spinner-btn-down';
            downBtn.setAttribute('aria-label', 'Decrement');
            downBtn.setAttribute('tabindex', '-1');
            
            // Add buttons to container
            spinnerContainer.appendChild(upBtn);
            spinnerContainer.appendChild(downBtn);
            
            // Add container to wrapper
            wrapper.appendChild(spinnerContainer);
            
            // Get step value (default to 1)
            const step = parseFloat(input.getAttribute('step')) || 1;
            const min = input.hasAttribute('min') ? parseFloat(input.getAttribute('min')) : null;
            const max = input.hasAttribute('max') ? parseFloat(input.getAttribute('max')) : null;
            
            // Increment function
            function increment() {
                let value = parseFloat(input.value) || 0;
                const newValue = value + step;
                
                if (max !== null && newValue > max) {
                    input.value = max;
                } else {
                    input.value = newValue;
                }
                
                // Trigger input event for form validation
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                
                updateButtonStates();
            }
            
            // Decrement function
            function decrement() {
                let value = parseFloat(input.value) || 0;
                const newValue = value - step;
                
                if (min !== null && newValue < min) {
                    input.value = min;
                } else {
                    input.value = newValue;
                }
                
                // Trigger input event for form validation
                input.dispatchEvent(new Event('input', { bubbles: true }));
                input.dispatchEvent(new Event('change', { bubbles: true }));
                
                updateButtonStates();
            }
            
            // Update button states based on min/max
            function updateButtonStates() {
                const value = parseFloat(input.value) || 0;
                
                if (min !== null) {
                    downBtn.disabled = value <= min;
                }
                if (max !== null) {
                    upBtn.disabled = value >= max;
                }
            }
            
            // Event listeners
            upBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                increment();
                input.focus();
            });
            
            downBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                decrement();
                input.focus();
            });
            
            // Update states on input change
            input.addEventListener('input', updateButtonStates);
            input.addEventListener('change', updateButtonStates);
            
            // Initial state update
            updateButtonStates();
        });
    }
    
    // ============================================
    // INITIALIZATION
    // ============================================
    
    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
            initDarkMode();
            initSearchFilter();
            initFeedbackModal();
            initMobileMenu();
            initSmoothInteractions();
            initLogoText();
            initNumberInputSpinners();
            });
        } else {
            // DOM already loaded
            initDarkMode();
            initSearchFilter();
            initFeedbackModal();
            initMobileMenu();
            initSmoothInteractions();
            initLogoText();
            initNumberInputSpinners();
        }
    }
    
    // Start initialization
    init();
    
})();

