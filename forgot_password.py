from flask import render_template, request, flash, redirect, url_for
from includes.db import query_db, get_db_connection
from includes.functions import validate_email
from includes.auth import hash_password
from datetime import datetime
import secrets
import smtplib
import ssl
import os
from email.message import EmailMessage

# FIX 2: load from .env not hardcoded
SMTP_SERVER     = os.environ.get('SMTP_SERVER',   'smtp.gmail.com')
SMTP_PORT       = int(os.environ.get('SMTP_PORT', 465))
SENDER_EMAIL    = os.environ.get('SMTP_EMAIL',    '')
SENDER_PASSWORD = os.environ.get('SMTP_PASSWORD', '')


def send_reset_email(user_email, reset_link):
    msg = EmailMessage()
    msg['Subject'] = 'Quak ALChicken - Password Reset Request'
    msg['From']    = SENDER_EMAIL
    msg['To']      = user_email
    msg.set_content(f"""Hi,

You requested a password reset for your ALChicken account.

Click the link below to set a new password:

{reset_link}

This link expires in 1 hour. If you did not request this, you can safely ignore this email.

- ALChicken Team
""")
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)


def forgot_password_page():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()

        if not email or not validate_email(email):
            flash('Please enter a valid email address', 'danger')
            return render_template('forgot_password.html')

        user = query_db("SELECT * FROM users WHERE email = ?", [email], one=True)

        # Always show same message - prevents email enumeration
        flash('If that email is registered, a reset link has been sent.', 'info')

        if user:
            token = secrets.token_urlsafe(32)
            conn  = get_db_connection()
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS password_resets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        token TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        used INTEGER DEFAULT 0,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)
                conn.execute("DELETE FROM password_resets WHERE user_id = ?", [user['user_id']])
                conn.execute(
                    "INSERT INTO password_resets (user_id, token) VALUES (?, ?)",
                    [user['user_id'], token]
                )
                conn.commit()

                reset_link = url_for('reset_password_page', token=token, _external=True)
                try:
                    send_reset_email(email, reset_link)
                except Exception as e:
                    print(f"[ERROR] Failed to send reset email to {email}: {e}")

            finally:
                conn.close()

        return redirect(url_for('login_page'))

    return render_template('forgot_password.html')


def reset_password_page(token):
    reset = query_db(
        """SELECT pr.*, u.email FROM password_resets pr
           JOIN users u ON pr.user_id = u.user_id
           WHERE pr.token = ? AND pr.used = 0""",
        [token], one=True
    )

    if not reset:
        flash('This reset link is invalid or has already been used.', 'danger')
        return redirect(url_for('forgot_password_page'))

    # FIX 3: handle SQLite datetime with or without microseconds
    created_str = reset['created_at']
    created = None
    for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
        try:
            created = datetime.strptime(created_str, fmt)
            break
        except ValueError:
            continue

    if not created:
        flash('This reset link has expired. Please request a new one.', 'danger')
        return redirect(url_for('forgot_password_page'))

    # FIX 1: use total_seconds() not .seconds (.seconds wraps at 86400)
    if (datetime.now() - created).total_seconds() > 3600:
        flash('This reset link has expired. Please request a new one.', 'danger')
        return redirect(url_for('forgot_password_page'))

    if request.method == 'POST':
        new_password     = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if len(new_password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return render_template('reset_password.html', token=token, email=reset['email'])

        if new_password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('reset_password.html', token=token, email=reset['email'])

        hashed = hash_password(new_password)
        conn   = get_db_connection()
        try:
            conn.execute(
                "UPDATE users SET password = ? WHERE user_id = ?",
                [hashed, reset['user_id']]
            )
            conn.execute(
                "UPDATE password_resets SET used = 1 WHERE token = ?",
                [token]
            )
            conn.commit()
        finally:
            conn.close()

        flash('Password reset successfully! Please login with your new password.', 'success')
        return redirect(url_for('login_page'))

    return render_template('reset_password.html', token=token, email=reset['email'])