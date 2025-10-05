from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, make_response
import json
import os
from datetime import datetime
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'TiTirana')



# Admin credentials (from environment variables for security)
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'TiTirana')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'TiTirana')

# Load tour data
def load_tours():
    try:
        with open('tours.json', 'r') as f:
            tours = json.load(f)
            return tours
    except FileNotFoundError:
        return []

# Save booking data
def save_booking(booking_data):
    try:
        # Load existing bookings
        if os.path.exists('bookings.json'):
            with open('bookings.json', 'r') as f:
                bookings = json.load(f)
        else:
            bookings = []

        # Add new booking
        bookings.append(booking_data)

        # Save back to file
        with open('bookings.json', 'w') as f:
            json.dump(bookings, f, indent=2)

        return True
    except Exception as e:
        print(f"Error saving booking: {e}")
        return False

# WhatsApp notification function
def send_whatsapp_notification(booking_data, tour):
    try:
        # Check if Twilio credentials are available
        twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        twilio_whatsapp_from = os.environ.get('TWILIO_WHATSAPP_FROM')
        admin_whatsapp = os.environ.get('ADMIN_WHATSAPP_NUMBER')

        if not all([twilio_account_sid, twilio_auth_token, twilio_whatsapp_from, admin_whatsapp]):
            print("WhatsApp notification skipped: Twilio credentials not configured")
            return False

        from twilio.rest import Client

        client = Client(twilio_account_sid, twilio_auth_token)

        # Format the message
        message_body = f"""
🎉 New Tour Booking!

Tour: {tour['title'] if tour else 'Unknown'}
Customer: {booking_data['user_name']}
Email: {booking_data['user_email']}
Phone: {booking_data['user_phone']}
People: {booking_data['number_of_people']}
Date/Time: {booking_data['preferred_date_time']}

Special Requests: {booking_data.get('special_requests', 'None')}

Booking ID: {booking_data['booking_id']}
        """.strip()

        # Send WhatsApp message
        message = client.messages.create(
            from_=f'whatsapp:{twilio_whatsapp_from}',
            body=message_body,
            to=f'whatsapp:{admin_whatsapp}'
        )

        print(f"WhatsApp notification sent successfully: {message.sid}")
        return True

    except Exception as e:
        print(f"Error sending WhatsApp notification: {e}")
        return False

@app.route('/')
def index():
    tours = load_tours()
    # Add meta tags for SEO
    meta_tags = {
        'title': 'Albania Walk Tours - Discover Albania with Us!',
        'description': 'Explore the best of Albania with our guided walking tours. From historical sites to stunning landscapes, find your perfect adventure.',
        'keywords': 'Albania tours, walking tours, Tirana tours, historical tours, adventure travel, Albania tourism'
    }
    return render_template('index.html', tours=tours, meta_tags=meta_tags)

@app.route('/tour/<tour_id>')
def tour_detail(tour_id):
    tours = load_tours()
    tour = next((t for t in tours if t['id'] == tour_id), None)
    if not tour:
        return redirect(url_for('index'))
    
    # Add meta tags for tour detail page SEO
    meta_tags = {
        'title': f"{tour.get('title', 'Tour Details')} - Albania Walk Tours",
        'description': tour.get('short_description', 'Discover this amazing tour in Albania.'),
        'keywords': f"Albania tour, {tour.get('title', '')}, guided tour, {tour.get('id', '')}"
    }
    return render_template('tour_detail.html', tour=tour, meta_tags=meta_tags)

@app.route('/about')
def about():
    # Add meta tags for about page SEO
    meta_tags = {
        'title': 'About Albania Walk Tours - Our Story',
        'description': 'Learn more about Albania Walk Tours, our mission, and our passion for showcasing the beauty of Albania.',
        'keywords': 'About us, Albania Walk Tours, our mission, travel company, Albania'
    }
    return render_template('about.html', meta_tags=meta_tags)

@app.route('/booking/<booking_id>')
def booking_confirmation(booking_id):
    try:
        with open('bookings.json', 'r') as f:
            bookings = json.load(f)

        booking = next((b for b in bookings if b['booking_id'] == booking_id), None)

        if not booking:
            return render_template('booking_not_found.html'), 404

        # Get tour details
        tours = load_tours()
        tour = next((t for t in tours if t['id'] == booking.get('tour_id')), None)

        # Get payment URL - use tour-specific link if available, otherwise use default
        payment_url = ''
        if tour and tour.get('paypal_link'):
            payment_url = tour['paypal_link']
        else:
            payment_url = os.environ.get('PAYPAL_PAYMENT_URL', 'https://www.paypal.com/ncp/payment/Q3PQ3TCYUA7L4')
        
        # Add meta tags for booking confirmation page SEO
        meta_tags = {
            'title': f'Booking Confirmation - {booking.get("booking_id", "")}',
            'description': f'Your booking for {tour.get("title", "a tour")} is confirmed. Please proceed to payment.',
            'keywords': 'booking confirmation, tour booking, payment, Albania tours'
        }

        return render_template('booking_confirmation.html', 
                             booking=booking, 
                             tour=tour,
                             payment_url=payment_url,
                             meta_tags=meta_tags)
    except FileNotFoundError:
        return render_template('booking_not_found.html'), 404

@app.route('/book', methods=['POST'])
def book_tour():
    # Validation
    required_fields = ['tour_id', 'user_name', 'user_email', 'user_phone', 'preferred_date_time', 'number_of_people']
    errors = []

    # Check required fields
    for field in required_fields:
        if not request.form.get(field) or not str(request.form.get(field)).strip():
            errors.append(f'{field.replace("_", " ").title()} is required')

    # Email validation
    import re
    email = request.form.get('user_email', '').strip()
    if email and not re.match(r'^[^\s@]+@[^\s@]+\.[^\s@]+$', email):
        errors.append('Please enter a valid email address')

    # Number of people validation
    try:
        num_people = int(request.form.get('number_of_people', 0))
        if num_people < 1 or num_people > 20:
            errors.append('Number of people must be between 1 and 20')
    except (ValueError, TypeError):
        errors.append('Number of people must be a valid number')
        num_people = 1

    # Tour exists validation
    tours = load_tours()
    tour_id = request.form.get('tour_id')
    if not any(t['id'] == tour_id for t in tours):
        errors.append('Invalid tour selected')

    if errors:
        return jsonify({'success': False, 'message': '; '.join(errors)})

    booking_data = {
        'booking_id': str(uuid.uuid4()),
        'tour_id': tour_id,
        'user_name': (request.form.get('user_name') or '').strip(),
        'user_email': email,
        'user_phone': (request.form.get('user_phone') or '').strip(),
        'number_of_people': num_people,
        'preferred_date_time': (request.form.get('preferred_date_time') or '').strip(),
        'special_requests': (request.form.get('special_requests') or '').strip(),
        'booking_time': datetime.now().isoformat(),
        'payment_status': 'pending'
    }

    if save_booking(booking_data):
        # Get tour details for the notification
        tour = next((t for t in tours if t['id'] == tour_id), None)

        # Send WhatsApp notification (requires Twilio credentials)
        send_whatsapp_notification(booking_data, tour)

        # PayPal payment link - use tour-specific link if available, otherwise use default
        payment_url = ''
        if tour and tour.get('paypal_link'):
            payment_url = tour['paypal_link']
        else:
            payment_url = os.environ.get('PAYPAL_PAYMENT_URL', 'https://www.paypal.com/ncp/payment/Q3PQ3TCYUA7L4')

        return jsonify({
            'success': True, 
            'message': 'Booking successful! Redirecting to payment...',
            'payment_url': payment_url,
            'booking_id': booking_data['booking_id']
        })
    else:
        return jsonify({'success': False, 'message': 'Booking failed due to server error. Please try again or contact us directly.'})

# Admin login decorator
def admin_required(f):
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials')

    # Add meta tags for admin login page SEO (though typically not indexed)
    meta_tags = {
        'title': 'Admin Login - Albania Walk Tours',
        'description': 'Administrator login page for Albania Walk Tours.',
        'robots': 'noindex, nofollow' # Prevent indexing of login page
    }
    return render_template('admin/login.html', meta_tags=meta_tags)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    tours = load_tours()

    # Load bookings
    try:
        with open('bookings.json', 'r') as f:
            bookings = json.load(f)
    except FileNotFoundError:
        bookings = []

    # Calculate recent bookings (last 7 days)
    from datetime import datetime, timedelta
    week_ago = datetime.now() - timedelta(days=7)
    recent_bookings_count = 0

    for booking in bookings:
        if 'booking_time' in booking:
            try:
                booking_date = datetime.fromisoformat(booking['booking_time'].replace('Z', '+00:00'))
                if booking_date >= week_ago:
                    recent_bookings_count += 1
            except (ValueError, TypeError):
                continue

    # Add meta tags for admin dashboard SEO (prevent indexing)
    meta_tags = {
        'title': 'Admin Dashboard - Albania Walk Tours',
        'robots': 'noindex, nofollow'
    }
    return render_template('admin/dashboard.html', 
                         tours=tours, 
                         bookings=bookings, 
                         recent_bookings_count=recent_bookings_count,
                         meta_tags=meta_tags)

@app.route('/admin/tours')
@admin_required
def admin_tours():
    tours = load_tours()
    # Add meta tags for admin tours page SEO (prevent indexing)
    meta_tags = {
        'title': 'Admin Tours Management - Albania Walk Tours',
        'robots': 'noindex, nofollow'
    }
    return render_template('admin/tours.html', tours=tours, meta_tags=meta_tags)

@app.route('/admin/tours/add', methods=['GET', 'POST'])
@admin_required
def admin_add_tour():
    if request.method == 'POST':
        tours = load_tours()

        new_tour = {
            'id': request.form.get('id') or '',
            'title': request.form.get('title') or '',
            'short_description': request.form.get('short_description') or '',
            'long_description': request.form.get('long_description') or '',
            'price': int(request.form.get('price') or 0),
            'duration': request.form.get('duration') or '',
            'starting_point': request.form.get('starting_point') or '',
            'schedule': (request.form.get('schedule') or '').split('\n'),
            'images': [img.strip() for img in (request.form.get('images') or '').split('\n') if img.strip()], # Process images, ensure no empty strings
            'highlights': [h.strip() for h in (request.form.get('highlights') or '').split('\n') if h.strip()], # Process highlights
            'included': [i.strip() for i in (request.form.get('included') or '').split('\n') if i.strip()], # Process included
            'meeting_point_details': request.form.get('meeting_point_details') or '',
            'languages': [lang.strip() for lang in (request.form.get('languages') or '').split(',') if lang.strip()],
            'paypal_link': request.form.get('paypal_link') or ''
        }
        
        # Basic validation for new tour fields
        if not new_tour['id'] or not new_tour['title'] or not new_tour['short_description']:
            flash('Error: Tour ID, Title, and Short Description are required.')
            return render_template('admin/add_tour.html', tour=new_tour) # Re-render with entered data

        tours.append(new_tour)

        try:
            with open('tours.json', 'w') as f:
                json.dump(tours, f, indent=2)
            flash('Tour added successfully!')
            return redirect(url_for('admin_tours'))
        except Exception as e:
            flash(f'Error saving tour: {e}')
            return render_template('admin/add_tour.html', tour=new_tour) # Re-render with entered data

    # Add meta tags for admin add tour page SEO (prevent indexing)
    meta_tags = {
        'title': 'Add New Tour - Albania Walk Tours',
        'robots': 'noindex, nofollow'
    }
    return render_template('admin/add_tour.html', meta_tags=meta_tags)

@app.route('/admin/tours/edit/<tour_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_tour(tour_id):
    tours = load_tours()
    tour = next((t for t in tours if t['id'] == tour_id), None)

    if not tour:
        flash('Tour not found')
        return redirect(url_for('admin_tours'))

    if request.method == 'POST':
        tour['title'] = request.form.get('title') or tour.get('title', '')
        tour['short_description'] = request.form.get('short_description') or tour.get('short_description', '')
        tour['long_description'] = request.form.get('long_description') or tour.get('long_description', '')
        tour['price'] = int(request.form.get('price') or tour.get('price', 0))
        tour['duration'] = request.form.get('duration') or tour.get('duration', '')
        tour['starting_point'] = request.form.get('starting_point') or tour.get('starting_point', '')
        tour['schedule'] = [s.strip() for s in (request.form.get('schedule') or '').split('\n') if s.strip()]
        tour['images'] = [img.strip() for img in (request.form.get('images') or '').split('\n') if img.strip()]
        tour['highlights'] = [h.strip() for h in (request.form.get('highlights') or '').split('\n') if h.strip()]
        tour['included'] = [i.strip() for i in (request.form.get('included') or '').split('\n') if i.strip()]
        tour['meeting_point_details'] = request.form.get('meeting_point_details') or tour.get('meeting_point_details', '')
        tour['languages'] = [lang.strip() for lang in (request.form.get('languages') or '').split(',') if lang.strip()]
        tour['paypal_link'] = request.form.get('paypal_link') or ''
        
        # Basic validation for edited tour fields
        if not tour['id'] or not tour['title'] or not tour['short_description']:
            flash('Error: Tour ID, Title, and Short Description are required.')
            return render_template('admin/edit_tour.html', tour=tour) # Re-render with edited data

        try:
            with open('tours.json', 'w') as f:
                json.dump(tours, f, indent=2)
            flash('Tour updated successfully!')
            return redirect(url_for('admin_tours'))
        except Exception as e:
            flash(f'Error saving tour: {e}')
            return render_template('admin/edit_tour.html', tour=tour) # Re-render with edited data

    # Add meta tags for admin edit tour page SEO (prevent indexing)
    meta_tags = {
        'title': f"Edit Tour: {tour.get('title', 'Unknown Tour')} - Albania Walk Tours",
        'robots': 'noindex, nofollow'
    }
    return render_template('admin/edit_tour.html', tour=tour, meta_tags=meta_tags)

@app.route('/admin/tours/delete/<tour_id>', methods=['POST'])
@admin_required
def admin_delete_tour(tour_id):
    tours = load_tours()
    initial_tour_count = len(tours)
    tours = [t for t in tours if t['id'] != tour_id]
    
    if len(tours) == initial_tour_count:
        flash('Tour not found. No changes made.')
        return redirect(url_for('admin_tours'))

    try:
        with open('tours.json', 'w') as f:
            json.dump(tours, f, indent=2)
        flash('Tour deleted successfully!')
    except Exception as e:
        flash(f'Error deleting tour: {e}')

    return redirect(url_for('admin_tours'))

@app.route('/admin/bookings')
@admin_required
def admin_bookings():
    try:
        with open('bookings.json', 'r') as f:
            bookings = json.load(f)
    except FileNotFoundError:
        bookings = []

    # Add meta tags for admin bookings page SEO (prevent indexing)
    meta_tags = {
        'title': 'Admin Bookings Management - Albania Walk Tours',
        'robots': 'noindex, nofollow'
    }
    return render_template('admin/bookings.html', bookings=bookings, meta_tags=meta_tags)

@app.route('/admin/bookings/delete/<booking_id>', methods=['POST'])
@admin_required
def admin_delete_booking(booking_id):
    try:
        with open('bookings.json', 'r') as f:
            bookings = json.load(f)

        initial_booking_count = len(bookings)
        bookings = [b for b in bookings if b['booking_id'] != booking_id]

        if len(bookings) == initial_booking_count:
            flash('Booking not found. No changes made.')
            return redirect(url_for('admin_bookings'))

        with open('bookings.json', 'w') as f:
            json.dump(bookings, f, indent=2)

        flash('Booking deleted successfully!')
    except FileNotFoundError:
        flash('No bookings found')
    except Exception as e:
        flash(f'Error deleting booking: {e}')

    return redirect(url_for('admin_bookings'))

@app.route('/admin/bookings/update-payment/<booking_id>', methods=['POST'])
@admin_required
def admin_update_payment_status(booking_id):
    try:
        with open('bookings.json', 'r') as f:
            bookings = json.load(f)

        new_status = request.form.get('payment_status', 'pending')

        booking_found = False
        for booking in bookings:
            if booking['booking_id'] == booking_id:
                booking['payment_status'] = new_status
                booking_found = True
                break

        if not booking_found:
            flash('Booking not found. Payment status not updated.')
            return redirect(url_for('admin_bookings'))

        with open('bookings.json', 'w') as f:
            json.dump(bookings, f, indent=2)

        flash(f'Payment status updated to {new_status}!')
    except FileNotFoundError:
        flash('Booking data not found. Payment status not updated.')
    except Exception as e:
        flash(f'Error updating payment status: {e}')

    return redirect(url_for('admin_bookings'))

# --- SEO Related Routes ---

@app.route('/sitemap.xml')
def sitemap():
    # Fetch all tours
    tours = load_tours()
    
    # Generate URLs
    urls = [
        url_for('index', _external=True),
        url_for('about', _external=True),
    ]
    for tour in tours:
        urls.append(url_for('tour_detail', tour_id=tour['id'], _external=True))

    # Create the XML content
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
"""
    for url in urls:
        xml_content += f"""
  <url>
    <loc>{url}</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%dT%H:%M:%S+00:00')}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
"""
    xml_content += "</urlset>"

    response = make_response(xml_content)
    response.headers['Content-Type'] = 'application/xml'
    return response

@app.route('/robots.txt')
def robots_txt():
    # Define robots.txt content
    robots_content = """User-agent: *
Allow: /

Sitemap: """ + url_for('sitemap', _external=True) + """

# Disallow admin pages from search engines
User-agent: *
Disallow: /admin/
"""
    response = make_response(robots_content)
    response.headers['Content-Type'] = 'text/plain'
    return response

if __name__ == '__main__':
    # Create dummy files if they don't exist
    if not os.path.exists('tours.json'):
        with open('tours.json', 'w') as f:
            json.dump([], f)
    if not os.path.exists('bookings.json'):
        with open('bookings.json', 'w') as f:
            json.dump([], f)
    
    # Create dummy admin/login.html if it doesn't exist
    if not os.path.exists('templates/admin/login.html'):
        os.makedirs('templates/admin', exist_ok=True)
        with open('templates/admin/login.html', 'w') as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Admin Login</title>
    <meta name="robots" content="noindex, nofollow">
</head>
<body>
    <h2>Admin Login</h2>
    {% with messages = get_flashed_messages() %}
      {% if messages %}
        <ul class=flashes>
        {% for message in messages %}
          <li>{{ message }}</li>
        {% endfor %}
        </ul>
      {% endif %}
    {% endwith %}
    <form method="post">
        Username: <input type="text" name="username"><br>
        Password: <input type="password" name="password"><br>
        <input type="submit" value="Login">
    </form>
</body>
</html>
""")
            
    # Create dummy admin/dashboard.html if it doesn't exist
    if not os.path.exists('templates/admin/dashboard.html'):
        os.makedirs('templates/admin', exist_ok=True)
        with open('templates/admin/dashboard.html', 'w') as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard</title>
    <meta name="robots" content="noindex, nofollow">
</head>
<body>
    <h1>Admin Dashboard</h1>
    <p><a href="{{ url_for('admin_tours') }}">Manage Tours</a></p>
    <p><a href="{{ url_for('admin_bookings') }}">Manage Bookings</a></p>
    <p><a href="{{ url_for('admin_logout') }}">Logout</a></p>

    <h2>Summary</h2>
    <p>Recent Bookings (Last 7 Days): {{ recent_bookings_count }}</p>
    
    <h3>Tours</h3>
    <ul>
        {% for tour in tours %}
            <li>{{ tour.title }} ({{ tour.id }})</li>
        {% else %}
            <li>No tours added yet.</li>
        {% endfor %}
    </ul>

    <h3>Bookings</h3>
    <ul>
        {% for booking in bookings %}
            <li>{{ booking.user_name }} - {{ booking.tour_id }} - {{ booking.booking_time }}</li>
        {% else %}
            <li>No bookings yet.</li>
        {% endfor %}
    </ul>
</body>
</html>
""")

    # Create dummy index.html if it doesn't exist
    if not os.path.exists('templates/index.html'):
        os.makedirs('templates', exist_ok=True)
        with open('templates/index.html', 'w') as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>{{ meta_tags.title }}</title>
    <meta name="description" content="{{ meta_tags.description }}">
    <meta name="keywords" content="{{ meta_tags.keywords }}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    {% include 'includes/og_tags.html' %}
</head>
<body>
    <header>
        <h1>Albania Walk Tours</h1>
        <nav>
            <a href="{{ url_for('index') }}">Home</a>
            <a href="{{ url_for('about') }}">About</a>
            <!-- Add other navigation links -->
        </nav>
    </header>
    
    <main>
        <h2>Explore Our Tours</h2>
        <div class="tours-grid">
            {% for tour in tours %}
            <div class="tour-card">
                <img src="{{ tour.images[0] if tour.images else url_for('static', filename='placeholder.jpg') }}" alt="{{ tour.title }} image">
                <h3>{{ tour.title }}</h3>
                <p>{{ tour.short_description }}</p>
                <a href="{{ url_for('tour_detail', tour_id=tour.id) }}" class="btn">View Details</a>
            </div>
            {% else %}
            <p>No tours available at the moment. Please check back soon!</p>
            {% endfor %}
        </div>
    </main>

    <footer>
        <p>&copy; 2023 Albania Walk Tours. All rights reserved.</p>
    </footer>
</body>
</html>
""")

    # Create dummy tour_detail.html if it doesn't exist
    if not os.path.exists('templates/tour_detail.html'):
        os.makedirs('templates', exist_ok=True)
        with open('templates/tour_detail.html', 'w') as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>{{ meta_tags.title }}</title>
    <meta name="description" content="{{ meta_tags.description }}">
    <meta name="keywords" content="{{ meta_tags.keywords }}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    {% include 'includes/og_tags.html' %}
</head>
<body>
    <header>
        <h1>{{ tour.title }}</h1>
        <nav>
            <a href="{{ url_for('index') }}">Home</a>
            <a href="{{ url_for('about') }}">About</a>
            <!-- Add other navigation links -->
        </nav>
    </header>

    <main>
        <div class="tour-details">
            {% if tour %}
                <h2>{{ tour.title }}</h2>
                {% for image in tour.images %}
                    <img src="{{ image }}" alt="{{ tour.title }} image" style="max-width: 500px; margin-bottom: 15px;">
                {% endfor %}
                
                <p><strong>Short Description:</strong> {{ tour.short_description }}</p>
                <p><strong>Long Description:</strong> {{ tour.long_description }}</p>
                <p><strong>Price:</strong> ${{ tour.price }}</p>
                <p><strong>Duration:</strong> {{ tour.duration }}</p>
                <p><strong>Starting Point:</strong> {{ tour.starting_point }}</p>
                
                <p><strong>Schedule:</strong></p>
                <ul>
                    {% for item in tour.schedule %}
                        <li>{{ item }}</li>
                    {% endfor %}
                </ul>

                <p><strong>Highlights:</strong></p>
                <ul>
                    {% for highlight in tour.highlights %}
                        <li>{{ highlight }}</li>
                    {% endfor %}
                </ul>
                
                <p><strong>Included:</strong></p>
                <ul>
                    {% for item in tour.included %}
                        <li>{{ item }}</li>
                    {% endfor %}
                </ul>

                <p><strong>Meeting Point Details:</strong> {{ tour.meeting_point_details }}</p>
                <p><strong>Languages:</strong> {{ tour.languages|join(', ') }}</p>

                <div class="booking-form">
                    <h3>Book This Tour</h3>
                    <form id="booking-form">
                        <input type="hidden" name="tour_id" value="{{ tour.id }}">
                        
                        <label for="user_name">Name:</label>
                        <input type="text" id="user_name" name="user_name" required>
                        
                        <label for="user_email">Email:</label>
                        <input type="email" id="user_email" name="user_email" required>
                        
                        <label for="user_phone">Phone:</label>
                        <input type="tel" id="user_phone" name="user_phone" required>
                        
                        <label for="preferred_date_time">Preferred Date & Time:</label>
                        <input type="datetime-local" id="preferred_date_time" name="preferred_date_time" required>
                        
                        <label for="number_of_people">Number of People:</label>
                        <input type="number" id="number_of_people" name="number_of_people" min="1" max="20" value="1" required>
                        
                        <label for="special_requests">Special Requests:</label>
                        <textarea id="special_requests" name="special_requests"></textarea>
                        
                        <button type="submit">Book Now</button>
                    </form>
                    <div id="booking-message"></div>
                </div>

            {% else %}
                <p>Tour not found.</p>
            {% endif %}
        </div>
    </main>

    <footer>
        <p>&copy; 2023 Albania Walk Tours. All rights reserved.</p>
    </footer>
    
    <script>
        document.getElementById('booking-form').addEventListener('submit', function(event) {
            event.preventDefault();
            const formData = new FormData(this);
            fetch('/book', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                const messageDiv = document.getElementById('booking-message');
                if (data.success) {
                    messageDiv.innerHTML = `<p style='color: green;'>${data.message}</p>`;
                    window.location.href = data.payment_url + '&booking_id=' + data.booking_id; // Redirect to payment
                } else {
                    messageDiv.innerHTML = `<p style='color: red;'>${data.message}</p>`;
                }
            })
            .catch(error => {
                document.getElementById('booking-message').innerHTML = `<p style='color: red;'>An error occurred. Please try again.</p>`;
                console.error('Error:', error);
            });
        });
    </script>
</body>
</html>
""")
    # Create dummy about.html if it doesn't exist
    if not os.path.exists('templates/about.html'):
        os.makedirs('templates', exist_ok=True)
        with open('templates/about.html', 'w') as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>{{ meta_tags.title }}</title>
    <meta name="description" content="{{ meta_tags.description }}">
    <meta name="keywords" content="{{ meta_tags.keywords }}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    {% include 'includes/og_tags.html' %}
</head>
<body>
    <header>
        <h1>About Albania Walk Tours</h1>
        <nav>
            <a href="{{ url_for('index') }}">Home</a>
            <a href="{{ url_for('about') }}">About</a>
            <!-- Add other navigation links -->
        </nav>
    </header>

    <main>
        <h2>Our Story</h2>
        <p>Albania Walk Tours was founded with a passion for showcasing the incredible beauty, rich history, and vibrant culture of Albania.</p>
        <p>We believe that the best way to experience a place is on foot, allowing you to connect with the local environment and people on a deeper level.</p>
        <p>Our team is dedicated to providing unique, memorable, and safe walking tours for every type of traveler.</p>
        
        <h3>Our Mission</h3>
        <p>To inspire exploration and appreciation of Albania through authentic and engaging walking experiences.</p>
        
        <h3>Contact Us</h3>
        <p>Email: info@albaniawalktours.com</p>
        <p>Phone: +355 XXX XXX XXX</p>
    </main>

    <footer>
        <p>&copy; 2023 Albania Walk Tours. All rights reserved.</p>
    </footer>
</body>
</html>
""")

    # Create dummy booking_confirmation.html if it doesn't exist
    if not os.path.exists('templates/booking_confirmation.html'):
        os.makedirs('templates', exist_ok=True)
        with open('templates/booking_confirmation.html', 'w') as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>{{ meta_tags.title }}</title>
    <meta name="description" content="{{ meta_tags.description }}">
    <meta name="keywords" content="{{ meta_tags.keywords }}">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    {% include 'includes/og_tags.html' %}
</head>
<body>
    <header>
        <h1>Booking Confirmation</h1>
        <nav>
            <a href="{{ url_for('index') }}">Home</a>
            <a href="{{ url_for('about') }}">About</a>
            <!-- Add other navigation links -->
        </nav>
    </header>

    <main>
        <h2>Thank you for your booking!</h2>
        {% if booking %}
            <p><strong>Booking ID:</strong> {{ booking.booking_id }}</p>
            <p><strong>Tour:</strong> {{ tour.title if tour else 'N/A' }}</p>
            <p><strong>Name:</strong> {{ booking.user_name }}</p>
            <p><strong>Email:</strong> {{ booking.user_email }}</p>
            <p><strong>Phone:</strong> {{ booking.user_phone }}</p>
            <p><strong>Number of People:</strong> {{ booking.number_of_people }}</p>
            <p><strong>Preferred Date & Time:</strong> {{ booking.preferred_date_time }}</p>
            <p><strong>Special Requests:</strong> {{ booking.special_requests }}</p>
            <p><strong>Booking Time:</strong> {{ booking.booking_time }}</p>
            <p><strong>Payment Status:</strong> {{ booking.payment_status }}</p>

            {% if booking.payment_status != 'paid' %}
                <p>Please proceed to payment to confirm your booking.</p>
                <a href="{{ payment_url }}" class="btn" target="_blank">Proceed to Payment</a>
            {% else %}
                <p>Your booking is confirmed and paid!</p>
            {% endif %}
        {% else %}
            <p>Booking details not found.</p>
        {% endif %}
    </main>

    <footer>
        <p>&copy; 2023 Albania Walk Tours. All rights reserved.</p>
    </footer>
</body>
</html>
""")

    # Create dummy booking_not_found.html if it doesn't exist
    if not os.path.exists('templates/booking_not_found.html'):
        os.makedirs('templates', exist_ok=True)
        with open('templates/booking_not_found.html', 'w') as f:
            f.write("""
<!DOCTYPE html>
<html>
<head>
    <title>Booking Not Found</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
    <header>
        <h1>Error</h1>
        <nav>
            <a href="{{ url_for('index') }}">Home</a>
            <a href="{{ url_for('about') }}">About</a>
        </nav>
    </header>
    <main>
        <h2>Booking Not Found</h2>
        <p>The booking you are looking for could not be found.</p>
        <p><a href="{{ url_for('index') }}">Go back to Home</a></p>
    </main>
    <footer>
        <p>&copy; 2023 Albania Walk Tours. All rights reserved.</p>
    </footer>
</body>
</html>
""")

    # Create dummy static/style.css if it doesn't exist
    if not os.path.exists('static/style.css'):
        os.makedirs('static', exist_ok=True)
        with open('static/style.css', 'w') as f:
            f.write("""
body { font-family: sans-serif; margin: 0; padding: 0; }
header { background-color: #f8f8f8; padding: 1em; text-align: center; }
nav a { margin: 0 1em; text-decoration: none; color: #333; }
main { padding: 2em; }
.tours-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; }
.tour-card { border: 1px solid #ddd; padding: 1em; text-align: center; }
.tour-card img { max-width: 100%; height: auto; margin-bottom: 1em; }
.btn { background-color: #4CAF50; color: white; padding: 0.8em 1.5em; text-decoration: none; border-radius: 5px; }
footer { background-color: #333; color: white; text-align: center; padding: 1em; margin-top: 2em; }
.tour-details img { max-width: 100%; height: auto; margin-bottom: 1em; }
.booking-form label { display: block; margin-top: 1em; }
.booking-form input, .booking-form textarea { width: calc(100% - 20px); padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 4px; }
.booking-form button { background-color: #2196F3; color: white; padding: 10px 15px; border: none; border-radius: 5px; cursor: pointer; margin-top: 1em; }
.flashes { list-style: none; padding: 0; margin-top: 1em; }
.flashes li { background-color: #f0ad4e; color: white; padding: 10px; margin-bottom: 5px; border-radius: 4px; }
""")
    
    # Create dummy includes/og_tags.html if it doesn't exist
    if not os.path.exists('templates/includes/og_tags.html'):
        os.makedirs('templates/includes', exist_ok=True)
        with open('templates/includes/og_tags.html', 'w') as f:
            f.write("""
{% if meta_tags %}
    <meta property="og:title" content="{{ meta_tags.title }}">
    <meta property="og:description" content="{{ meta_tags.description }}">
    {# Add og:image if available #}
    {% if meta_tags.image %}
        <meta property="og:image" content="{{ meta_tags.image }}">
    {% endif %}
    <meta property="og:url" content="{{ request.url }}">
    <meta property="og:type" content="website">
{% endif %}
""")


    app.run(host='0.0.0.0', port=5000, debug=True)