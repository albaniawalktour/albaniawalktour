// Mobile Navigation Toggle
document.addEventListener('DOMContentLoaded', function() {
    const hamburger = document.getElementById('hamburger');
    const navMenu = document.getElementById('nav-menu');

    // Language toggle functionality
    const languageToggle = document.getElementById('language-toggle');
    const languageDropdown = document.getElementById('language-dropdown');

    if (languageToggle && languageDropdown) {
        languageToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            languageDropdown.classList.toggle('active');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function(event) {
            if (!languageToggle.contains(event.target) && !languageDropdown.contains(event.target)) {
                languageDropdown.classList.remove('active');
            }
        });

        // Prevent dropdown from closing when clicking inside
        languageDropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }

    if (hamburger && navMenu) {
        hamburger.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            hamburger.classList.toggle('active');
        });

        // Close menu when clicking on a link
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navMenu.classList.remove('active');
                hamburger.classList.remove('active');
            });
        });

        // Close menu when clicking outside
        document.addEventListener('click', function(event) {
            if (!hamburger.contains(event.target) && !navMenu.contains(event.target)) {
                navMenu.classList.remove('active');
                hamburger.classList.remove('active');
            }
        });
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            
            // Skip if href is just "#" or empty
            if (href === '#' || !href) {
                e.preventDefault();
                return;
            }
            
            // If we're not on the homepage, go to homepage first
            if (window.location.pathname !== '/' && href.startsWith('#')) {
                window.location.href = '/' + href;
                return;
            }
            
            e.preventDefault();
            
            // Validate selector before using it
            if (href.length > 1) {
                const target = document.querySelector(href);
                if (target) {
                    const navbarHeight = document.querySelector('.navbar').offsetHeight;
                    const targetPosition = target.offsetTop - navbarHeight - 20;
                    
                    window.scrollTo({
                        top: targetPosition,
                        behavior: 'smooth'
                    });
                }
            }
        });
    });

    // Navbar background on scroll
    window.addEventListener('scroll', function() {
        const navbar = document.querySelector('.navbar');
        if (window.scrollY > 50) {
            navbar.style.background = 'rgba(255, 255, 255, 0.98)';
        } else {
            navbar.style.background = 'rgba(255, 255, 255, 0.95)';
        }
    });

    // Booking form functionality
    const bookingForm = document.getElementById('booking-form');
    if (bookingForm) {
        bookingForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Basic client-side validation
            const requiredFields = ['user_name', 'user_email', 'user_phone', 'preferred_date_time', 'number_of_people'];
            let isValid = true;
            
            requiredFields.forEach(fieldName => {
                const field = this.querySelector(`[name="${fieldName}"]`);
                if (!field || !field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#ff3b30';
                } else {
                    field.style.borderColor = '#d2d2d7';
                }
            });
            
            // Email validation
            const email = this.querySelector('[name="user_email"]');
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (email && !emailRegex.test(email.value)) {
                isValid = false;
                email.style.borderColor = '#ff3b30';
            }
            
            if (!isValid) {
                alert('Please fill in all required fields correctly.');
                return;
            }
            
            // Show loading state
            const submitButton = this.querySelector('.book-button');
            const originalText = submitButton.textContent;
            submitButton.textContent = 'Booking...';
            submitButton.disabled = true;
            
            const formData = new FormData(this);
            
            fetch('/book', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    window.location.href = `/booking/${data.booking_id}`;
                } else {
                    alert(data.message || 'Booking failed. Please try again or contact us directly.');
                    submitButton.textContent = originalText;
                    submitButton.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again or contact us directly.');
                submitButton.textContent = originalText;
                submitButton.disabled = false;
            });
        });
    }

    // Add loading animation to buttons
    document.querySelectorAll('.cta-button, .tour-button').forEach(button => {
        button.addEventListener('click', function(e) {
            if (this.href && this.href.includes('#')) {
                return; // Allow smooth scroll
            }
            
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = '';
            }, 150);
        });
    });
});

// Translation Functions
function toggleTranslateOptions() {
    const dropdown = document.getElementById('translate-dropdown');
    if (dropdown) {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    }
}

function translatePage(event, lang) {
    event.preventDefault();
    const currentUrl = window.location.href;
    const googleTranslateUrl = `https://translate.google.com/translate?sl=auto&tl=${lang}&u=${encodeURIComponent(currentUrl)}`;
    window.location.href = googleTranslateUrl;
}

function goToOriginal(event) {
    event.preventDefault();
    // Remove any Google Translate parameters from URL
    const currentUrl = window.location.href;
    const cleanUrl = currentUrl.split('?')[0];
    window.location.href = cleanUrl;
}

// Close translate dropdown when clicking outside
document.addEventListener('click', function(event) {
    const translateToggle = document.getElementById('translate-toggle');
    const translateDropdown = document.getElementById('translate-dropdown');
    
    if (translateToggle && translateDropdown && 
        !translateToggle.contains(event.target) && 
        !translateDropdown.contains(event.target)) {
        translateDropdown.style.display = 'none';
    }
});

// AI Assistant Functions
function toggleAIAssistant() {
    const panel = document.getElementById('ai-assistant-panel');
    if (panel) {
        panel.style.display = panel.style.display === 'none' ? 'flex' : 'none';
    }
}

function handleAIKeyPress(event) {
    if (event.key === 'Enter') {
        sendAIMessage();
    }
}

function sendAIMessage() {
    const input = document.getElementById('ai-input');
    const chatContainer = document.getElementById('ai-chat-container');
    
    if (!input || !chatContainer) return;
    
    const message = input.value.trim();
    if (!message) return;
    
    // Add user message to chat
    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'ai-message user';
    userMessageDiv.textContent = message;
    chatContainer.appendChild(userMessageDiv);
    
    // Clear input
    input.value = '';
    
    // Scroll to bottom
    chatContainer.scrollTop = chatContainer.scrollHeight;
    
    // Simulate AI response (you can replace this with actual API call)
    setTimeout(() => {
        const assistantMessage = generateAIResponse(message.toLowerCase());
        const assistantMessageDiv = document.createElement('div');
        assistantMessageDiv.className = 'ai-message assistant';
        assistantMessageDiv.innerHTML = assistantMessage;
        chatContainer.appendChild(assistantMessageDiv);
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }, 1000);
}

function generateAIResponse(userMessage) {
    // Simple keyword-based responses - you can enhance this with actual AI
    if (userMessage.includes('1 day') || userMessage.includes('one day')) {
        return `I recommend our <strong>Tirana Food & Culture Experience</strong> - a perfect day exploring local cuisine and culture! <br><br>
                <a href="/tour/food-culture-tour" class="tour-link">View Tour Details</a>`;
    }
    
    if (userMessage.includes('beach') || userMessage.includes('coast') || userMessage.includes('riviera')) {
        return `For beach lovers, check out our <strong>Albanian Riviera tours</strong>! Crystal clear waters and stunning coastlines await. <br><br>
                <a href="/#tours" class="tour-link">Browse Beach Tours</a>`;
    }
    
    if (userMessage.includes('history') || userMessage.includes('historical') || userMessage.includes('unesco')) {
        return `Perfect! Try our <strong>Butrint Archaeological Tour</strong> or <strong>Berat Wine & Culture Tour</strong> - both feature UNESCO World Heritage sites! <br><br>
                <a href="/tour/butrint-archaeological-tour" class="tour-link">View Archaeological Tour</a>`;
    }
    
    if (userMessage.includes('mountain') || userMessage.includes('hiking') || userMessage.includes('nature')) {
        return `Nature enthusiast? Our <strong>Dajti Mountain Adventure</strong> offers stunning views and hiking trails! <br><br>
                <a href="/tour/dajti-mountain-adventure" class="tour-link">Explore Mountain Tour</a>`;
    }
    
    if (userMessage.includes('week') || userMessage.includes('7 day') || userMessage.includes('multi')) {
        return `For a comprehensive experience, try our <strong>7-Day Albania Grand Tour</strong> - covering the best of Albania! <br><br>
                <a href="/tour/7-day-albania-grand-tour" class="tour-link">View 7-Day Tour</a>`;
    }
    
    if (userMessage.includes('custom') || userMessage.includes('personalized') || userMessage.includes('design')) {
        return `We can create a <strong>Custom Tour</strong> tailored to your interests and budget! <br><br>
                <a href="/tour/custom-tour-albania" class="tour-link">Design Your Tour</a>`;
    }
    
    // Default response
    return `Great question! Based on your interests, I'd recommend browsing our tour collection. We offer:
            <br>• Cultural & Historical Tours
            <br>• Food & Wine Experiences  
            <br>• Nature & Adventure Tours
            <br>• Beach & Coastal Trips
            <br>• Custom Personalized Tours
            <br><br>What type of experience interests you most? Or <a href="/#tours" class="tour-link">browse all tours</a>`;
}

// Close AI panel when clicking outside
document.addEventListener('click', function(event) {
    const aiToggle = document.getElementById('ai-assistant-toggle');
    const aiPanel = document.getElementById('ai-assistant-panel');
    
    if (aiToggle && aiPanel && 
        !aiToggle.contains(event.target) && 
        !aiPanel.contains(event.target)) {
        aiPanel.style.display = 'none';
    }
});