# Tirana Walk Tour - Flask Web Application

## Overview
A multilingual Flask web application for tour booking in Albania. The application features tour listings, booking functionality, and an admin panel for managing tours and bookings.

## Recent Changes
- **2025-10-04**: Added PayPal payment integration and WhatsApp notifications
  - Integrated PayPal payment link for immediate checkout after booking
  - Added Twilio WhatsApp notification system to alert admin of new bookings
  - Installed Twilio library for WhatsApp messaging
  - Updated booking flow to redirect to PayPal payment after form submission
- **2025-10-04**: Fresh GitHub clone successfully configured for Replit
  - Synchronized dependencies using uv package manager
  - Created Flask Server workflow running on port 5000 with webview output
  - Added .gitignore file for Python project
  - Configured autoscale deployment with gunicorn for production
  - Verified application is running correctly
- **2025-09-19**: Project imported and configured for Replit environment
- Security improvement: Replaced hardcoded admin credentials with environment variables

## User Preferences
- Follow existing Flask project structure and conventions
- Maintain internationalization (i18n) support for multiple languages
- Keep JSON-based data storage for tours and bookings as per current implementation

## Project Architecture

### Technology Stack
- **Backend**: Flask 3.1.2 with Flask-Babel for internationalization
- **Database**: JSON files (tours.json, bookings.json) for data persistence
- **Frontend**: HTML templates with Bootstrap CSS framework
- **Languages**: Python 3.11+

### Key Features
- Multi-language support (English, German, Italian, Arabic)
- Tour booking system with validation
- **PayPal payment integration** - Immediate checkout after booking
- **WhatsApp notifications** - Admin receives booking alerts via WhatsApp (requires Twilio setup)
- Admin panel for tour and booking management
- Responsive design with modern UI

### File Structure
```
├── app.py                 # Main Flask application
├── main.py               # Application entry point
├── pyproject.toml        # Python dependencies (uv-based)
├── tours.json            # Tour data storage
├── bookings.json         # Booking data storage
├── static/               # CSS, JS, and static assets
├── templates/            # Jinja2 HTML templates
├── translations/         # i18n message files
└── babel.cfg            # Babel configuration for translations
```

### Environment Variables
- `SESSION_SECRET`: Flask session secret key
- `ADMIN_USERNAME`: Admin login username (default: TiTirana)
- `ADMIN_PASSWORD`: Admin login password (default: TiTirana)

#### Payment Integration
- `PAYPAL_PAYMENT_URL`: PayPal payment link URL (default: https://www.paypal.com/ncp/payment/Q3PQ3TCYUA7L4)

#### WhatsApp Notifications (Optional - requires Twilio account)
- `TWILIO_ACCOUNT_SID`: Twilio account SID
- `TWILIO_AUTH_TOKEN`: Twilio authentication token
- `TWILIO_WHATSAPP_FROM`: Twilio WhatsApp-enabled phone number (e.g., +14155238886)
- `ADMIN_WHATSAPP_NUMBER`: Admin WhatsApp number to receive booking notifications (e.g., +355XXXXXXXXX)

**Note:** WhatsApp notifications will be skipped if Twilio credentials are not configured. The booking system works without them.

### Development Server
- Runs on `0.0.0.0:5000` for Replit compatibility
- Debug mode enabled for development
- Automatic reloading on code changes

### Production Deployment
- Configured for autoscale deployment target
- Uses gunicorn WSGI server
- Optimized for stateless web application hosting

## Current Status
✅ Application successfully running on port 5000
✅ All dependencies installed and configured (including Twilio)
✅ PayPal payment integration active
✅ WhatsApp notification code implemented (awaiting Twilio credentials)
✅ Security vulnerabilities addressed
✅ Deployment configuration completed
✅ Ready for production deployment

## Setup Instructions

### To Enable WhatsApp Notifications:
1. Create a Twilio account at https://www.twilio.com
2. Get a WhatsApp-enabled phone number from Twilio
3. Add the following secrets in Replit:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`
   - `TWILIO_WHATSAPP_FROM`
   - `ADMIN_WHATSAPP_NUMBER`
4. Restart the application

### To Change PayPal Payment Link:
1. Add/update the `PAYPAL_PAYMENT_URL` secret with your PayPal payment link
2. Restart the application