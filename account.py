from flask import render_template, request, session, redirect, url_for, flash
from includes.db import query_db, get_db_connection
from includes.auth import login_required, hash_password, verify_password
from includes.functions import validate_jamaica_phone
from datetime import datetime, timedelta

@login_required
def account_page():
    if request.method == 'POST':
        action = request.form.get('action')
        user   = query_db("SELECT * FROM users WHERE user_id = ?", [session['user_id']], one=True)

        if action == 'update_profile':
            name    = request.form.get('name', '').strip()
            phone   = request.form.get('phone', '').strip()
            address = request.form.get('address', '').strip()

            if not name:
                flash('Name is required', 'danger')
            elif phone and not validate_jamaica_phone(phone):
                flash('Invalid phone number format. Use 876-XXX-XXXX', 'danger')
            else:
                conn = get_db_connection()
                conn.execute(
                    "UPDATE users SET name = ?, phone = ?, address = ? WHERE user_id = ?",
                    [name, phone, address, session['user_id']]
                )
                conn.commit()
                conn.close()
                session['user_name'] = name
                flash('Profile updated successfully', 'success')

        elif action == 'change_password':
            current_password = request.form.get('current_password')
            new_password     = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not verify_password(current_password, user['password']):
                flash('Current password is incorrect', 'danger')
            elif new_password != confirm_password:
                flash('New passwords do not match', 'danger')
            elif len(new_password) < 6:
                flash('Password must be at least 6 characters', 'danger')
            else:
                hashed = hash_password(new_password)
                conn   = get_db_connection()
                conn.execute(
                    "UPDATE users SET password = ? WHERE user_id = ?",
                    [hashed, session['user_id']]
                )
                conn.commit()
                conn.close()
                flash('Password changed successfully', 'success')

        elif action == 'delete_account':
            # FIX: soft delete - mark as deleted for 30 days instead of hard delete
            # Orders and data are preserved. If user re-registers with same email
            # within 30 days, data is automatically restored.
            deleted_at   = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            restore_by   = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d %H:%M:%S')
            conn = get_db_connection()
            try:
                # Ensure columns exist (safe to run if already added)
                try:
                    conn.execute("ALTER TABLE users ADD COLUMN deleted_at DATETIME DEFAULT NULL")
                    conn.execute("ALTER TABLE users ADD COLUMN restore_by DATETIME DEFAULT NULL")
                    conn.commit()
                except Exception:
                    pass  # Columns already exist

                conn.execute(
                    "UPDATE users SET deleted_at = ?, restore_by = ? WHERE user_id = ?",
                    [deleted_at, restore_by, session['user_id']]
                )
                conn.commit()
            finally:
                conn.close()

            session.clear()
            flash('Your account has been deleted. Your order history will be kept for 30 days. '
                  'If you re-register with the same email within 30 days, your data will be restored.',
                  'info')
            return redirect(url_for('home_page'))

        return redirect(url_for('account_page'))

    # GET - load fresh user data
    user   = query_db("SELECT * FROM users WHERE user_id = ?", [session['user_id']], one=True)
    orders = query_db(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY order_date DESC LIMIT 10",
        [session['user_id']]
    )
    return render_template('account.html', user=user, orders=orders)