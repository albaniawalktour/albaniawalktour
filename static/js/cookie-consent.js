
// Cookie Consent Management
(function() {
    'use strict';

    const COOKIE_NAME = 'cookie_consent';
    const COOKIE_EXPIRY_DAYS = 365;

    // Check if consent has been given
    function hasConsent() {
        return getCookie(COOKIE_NAME) !== null;
    }

    // Get cookie value
    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // Set cookie
    function setCookie(name, value, days) {
        const date = new Date();
        date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
        const expires = `expires=${date.toUTCString()}`;
        document.cookie = `${name}=${value};${expires};path=/;SameSite=Lax`;
    }

    // Show cookie banner
    function showCookieBanner() {
        const banner = document.getElementById('cookie-consent');
        if (banner) {
            setTimeout(() => {
                banner.classList.add('show');
            }, 500);
        }
    }

    // Hide cookie banner
    function hideCookieBanner() {
        const banner = document.getElementById('cookie-consent');
        if (banner) {
            banner.classList.remove('show');
            setTimeout(() => {
                banner.style.display = 'none';
            }, 300);
        }
    }

    // Accept cookies
    function acceptCookies() {
        setCookie(COOKIE_NAME, 'accepted', COOKIE_EXPIRY_DAYS);
        hideCookieBanner();
        
        // Initialize analytics or other tracking here if needed
        console.log('Cookies accepted');
    }

    // Decline cookies
    function declineCookies() {
        setCookie(COOKIE_NAME, 'declined', COOKIE_EXPIRY_DAYS);
        hideCookieBanner();
        
        // Disable analytics or other tracking here if needed
        console.log('Cookies declined');
    }

    // Initialize
    document.addEventListener('DOMContentLoaded', function() {
        if (!hasConsent()) {
            showCookieBanner();
        }

        // Accept button
        const acceptBtn = document.getElementById('cookie-accept');
        if (acceptBtn) {
            acceptBtn.addEventListener('click', acceptCookies);
        }

        // Decline button
        const declineBtn = document.getElementById('cookie-decline');
        if (declineBtn) {
            declineBtn.addEventListener('click', declineCookies);
        }
    });
})();
