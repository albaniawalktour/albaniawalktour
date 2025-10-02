# Tirana Walk Tour - Flask Web Application

## Overview
A multilingual Flask web application for tour booking in Albania. The application features tour listings, booking functionality, and an admin panel for managing tours and bookings.

## Recent Changes
- **2025-09-19**: Project imported and configured for Replit environment
- Security improvement: Replaced hardcoded admin credentials with environment variables
- Configured proper workflow for port 5000 with webview output
- Set up deployment configuration using gunicorn for production

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
- `ADMIN_USERNAME`: Admin login username (default: admin)
- `ADMIN_PASSWORD`: Admin login password (default: admin123)

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
✅ All dependencies installed and configured
✅ Security vulnerabilities addressed
✅ Deployment configuration completed
✅ Ready for production deployment