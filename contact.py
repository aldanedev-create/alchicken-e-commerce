from flask import render_template, request, jsonify
from includes.db import query_db
from includes.functions import validate_email, sanitize_input

def contact_page():
    """Renders the contact page. Form submits via JS only."""
    return render_template('contact.html', farmer_number='876-555-0123')


def save_contact_message():
    """
    POST /contact/save
    Called by contact.html JS to save message to database.
    """
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'No data received'}), 400

    name    = sanitize_input(data.get('name', ''))
    email   = sanitize_input(data.get('email', ''))
    subject = sanitize_input(data.get('subject', 'Inquiry'))
    message = sanitize_input(data.get('message', ''))

    if not all([name, email, message]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    if not validate_email(email):
        return jsonify({'success': False, 'error': 'Invalid email address'}), 400

    try:
        query_db(
            "INSERT INTO messages (name, email, subject, message) VALUES (?, ?, ?, ?)",
            [name, email, subject, message]
        )
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500