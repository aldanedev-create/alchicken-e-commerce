import os
import secrets
import smtplib
import ssl
from datetime import datetime
from email.message import EmailMessage
from flask import session, redirect, url_for, flash, render_template, request, jsonify
from includes.db import query_db, get_db_connection
from includes.auth import login_required


def generate_2fa_code():
    return str(secrets.randbelow(900000) + 100000)


def store_2fa_code(user_id, code):
    conn = get_db_connection()
    try:
        conn.execute("DELETE FROM two_fa_codes WHERE user_id = ?", [user_id])
        conn.execute(
            "INSERT INTO two_fa_codes (user_id, code) VALUES (?, ?)",
            [user_id, code]
        )
        conn.commit()
    finally:
        conn.close()


def verify_2fa_code(user_id, submitted_code):
    record = query_db(
        "SELECT * FROM two_fa_codes WHERE user_id = ? AND code = ? AND used = 0",
        [user_id, submitted_code], one=True
    )
    if not record:
        return False

    created_str = record['created_at']
    created     = None
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            created = datetime.strptime(created_str, fmt)
            break
        except ValueError:
            continue

    if not created or (datetime.now() - created).total_seconds() > 600:
        return False

    conn = get_db_connection()
    try:
        conn.execute("UPDATE two_fa_codes SET used = 1 WHERE id = ?", [record['id']])
        conn.commit()
    finally:
        conn.close()
    return True


def send_2fa_email(user_email, code, user_name):
    sender_email    = os.environ.get('SMTP_EMAIL', '')
    sender_password = os.environ.get('SMTP_PASSWORD', '')

    if not sender_email or not sender_password:
        raise Exception('SMTP credentials not configured in .env')

    msg            = EmailMessage()
    msg['Subject'] = 'ALChicken - Your Verification Code'
    msg['From']    = sender_email
    msg['To']      = user_email
    msg.set_content(f"""Hi {user_name},

Your ALChicken verification code is:

    {code}

This code expires in 10 minutes. Do not share it with anyone.

If you did not attempt to login, please change your password immediately.

- ALChicken Team
""")
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)



def two_fa_verify_page():
    if 'pending_user_id' not in session:
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        submitted = request.form.get('code', '').strip().replace(' ', '')
        user_id   = session['pending_user_id']

        if verify_2fa_code(user_id, submitted):
            user = query_db("SELECT * FROM users WHERE user_id = ?", [user_id], one=True)
            session.pop('pending_user_id',   None)
            session.pop('pending_2fa_method', None)
            session['user_id']    = user['user_id']
            session['user_name']  = user['name']
            session['user_role']  = user['role']
            session['user_email'] = user['email']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('home_page'))
        else:
            flash('Invalid or expired code. Please try again.', 'danger')

    method = session.get('pending_2fa_method', 'email')
    return render_template('two_fa_verify.html', method=method)


def two_fa_resend():
    # FIX: silently accept JSON body (sent by JS fetch with Content-Type: application/json)
    # Flask requires get_json() or the body is ignored — this was causing 415 errors
    request.get_json(silent=True)
 
    if 'pending_user_id' not in session:
        return jsonify({'success': False, 'error': 'Session expired'}), 400
 
    user_id = session['pending_user_id']
    user    = query_db("SELECT * FROM users WHERE user_id = ?", [user_id], one=True)
 
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
 
    code = generate_2fa_code()
    store_2fa_code(user_id, code)
 
    try:
        send_2fa_email(user['email'], code, user['name'])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
 

@login_required
def two_fa_settings():
    action = request.form.get('action')

    if action == 'enable_2fa':
        conn = get_db_connection()
        try:
            conn.execute(
                "UPDATE users SET two_fa_enabled = 1, two_fa_method = 'email' WHERE user_id = ?",
                [session['user_id']]
            )
            conn.commit()
        finally:
            conn.close()
        flash('Two-step verification enabled via Email.', 'success')

    elif action == 'disable_2fa':
        conn = get_db_connection()
        try:
            conn.execute(
                "UPDATE users SET two_fa_enabled = 0, two_fa_method = NULL WHERE user_id = ?",
                [session['user_id']]
            )
            conn.commit()
        finally:
            conn.close()
        flash('Two-step verification disabled.', 'success')

    return redirect(url_for('account_page') + '#security')


