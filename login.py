from flask import render_template, request, redirect, url_for, flash, session
from includes.auth import login_user
from includes.db import query_db


def login_page():
    if request.method == 'POST':
        email     = request.form.get('email', '').strip()
        password  = request.form.get('password', '')
        next_page = request.args.get('next', url_for('home_page'))

        success, error = login_user(email, password)

        if success:
            # Check if this user has 2FA enabled
            user = query_db(
                "SELECT user_id, name, email, role, two_fa_enabled FROM users WHERE email = ?",
                [email], one=True
            )

            if user and user['two_fa_enabled']:
                from two_fa import generate_2fa_code, store_2fa_code, send_2fa_email

                # Clear session set by login_user - not fully logged in yet
                session.clear()
                session.permanent = True  # re-set AFTER clear


                code = generate_2fa_code()
                store_2fa_code(user['user_id'], code)

                session['pending_user_id']    = user['user_id']
                session['pending_2fa_method'] = 'email'

                try:
                    send_2fa_email(user['email'], code, user['name'])
                    flash(f'A verification code has been sent to {user["email"]}.', 'info')
                except Exception as e:
                    print(f'[ERROR] 2FA send failed: {e}')
                    flash('Could not send verification code. Please try again.', 'danger')
                    return render_template('login.html')

                return redirect(url_for('two_fa_verify_page'))

            else:
                flash('Logged in successfully!', 'success')
                return redirect(next_page)
        else:
            flash(error, 'danger')

    return render_template('login.html')