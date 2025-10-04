from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
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
    return render_template('index.html', tours=tours)

@app.route('/tour/<tour_id>')
def tour_detail(tour_id):
    tours = load_tours()
    tour = next((t for t in tours if t['id'] == tour_id), None)
    if not tour:
        return redirect(url_for('index'))
    return render_template('tour_detail.html', tour=tour)

@app.route('/about')
def about():
    return render_template('about.html')

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
        
        return render_template('booking_confirmation.html', 
                             booking=booking, 
                             tour=tour,
                             payment_url=payment_url)
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
    
    return render_template('admin/login.html')

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
    
    return render_template('admin/dashboard.html', 
                         tours=tours, 
                         bookings=bookings, 
                         recent_bookings_count=recent_bookings_count)

@app.route('/admin/tours')
@admin_required
def admin_tours():
    tours = load_tours()
    return render_template('admin/tours.html', tours=tours)

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
            'images': (request.form.get('images') or '').split('\n'),
            'highlights': (request.form.get('highlights') or '').split('\n'),
            'included': (request.form.get('included') or '').split('\n'),
            'meeting_point_details': request.form.get('meeting_point_details') or '',
            'languages': (request.form.get('languages') or '').split(','),
            'paypal_link': request.form.get('paypal_link') or ''
        }
        
        tours.append(new_tour)
        
        with open('tours.json', 'w') as f:
            json.dump(tours, f, indent=2)
        
        flash('Tour added successfully!')
        return redirect(url_for('admin_tours'))
    
    return render_template('admin/add_tour.html')

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
        tour['schedule'] = (request.form.get('schedule') or '').split('\n')
        tour['images'] = (request.form.get('images') or '').split('\n')
        tour['highlights'] = (request.form.get('highlights') or '').split('\n')
        tour['included'] = (request.form.get('included') or '').split('\n')
        tour['meeting_point_details'] = request.form.get('meeting_point_details') or tour.get('meeting_point_details', '')
        tour['languages'] = [lang.strip() for lang in (request.form.get('languages') or '').split(',') if lang.strip()]
        tour['paypal_link'] = request.form.get('paypal_link') or ''
        
        with open('tours.json', 'w') as f:
            json.dump(tours, f, indent=2)
        
        flash('Tour updated successfully!')
        return redirect(url_for('admin_tours'))
    
    return render_template('admin/edit_tour.html', tour=tour)

@app.route('/admin/tours/delete/<tour_id>', methods=['POST'])
@admin_required
def admin_delete_tour(tour_id):
    tours = load_tours()
    tours = [t for t in tours if t['id'] != tour_id]
    
    with open('tours.json', 'w') as f:
        json.dump(tours, f, indent=2)
    
    flash('Tour deleted successfully!')
    return redirect(url_for('admin_tours'))

@app.route('/admin/bookings')
@admin_required
def admin_bookings():
    try:
        with open('bookings.json', 'r') as f:
            bookings = json.load(f)
    except FileNotFoundError:
        bookings = []
    
    return render_template('admin/bookings.html', bookings=bookings)

@app.route('/admin/bookings/delete/<booking_id>', methods=['POST'])
@admin_required
def admin_delete_booking(booking_id):
    try:
        with open('bookings.json', 'r') as f:
            bookings = json.load(f)
        
        bookings = [b for b in bookings if b['booking_id'] != booking_id]
        
        with open('bookings.json', 'w') as f:
            json.dump(bookings, f, indent=2)
        
        flash('Booking deleted successfully!')
    except FileNotFoundError:
        flash('No bookings found')
    
    return redirect(url_for('admin_bookings'))

@app.route('/admin/bookings/update-payment/<booking_id>', methods=['POST'])
@admin_required
def admin_update_payment_status(booking_id):
    try:
        with open('bookings.json', 'r') as f:
            bookings = json.load(f)
        
        new_status = request.form.get('payment_status', 'pending')
        
        for booking in bookings:
            if booking['booking_id'] == booking_id:
                booking['payment_status'] = new_status
                break
        
        with open('bookings.json', 'w') as f:
            json.dump(bookings, f, indent=2)
        
        flash(f'Payment status updated to {new_status}!')
    except FileNotFoundError:
        flash('Booking not found')
    
    return redirect(url_for('admin_bookings'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)