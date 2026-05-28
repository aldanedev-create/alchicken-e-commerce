import bcrypt
from functools import wraps
from flask import session, redirect, url_for, flash
from includes.db import query_db, get_db_connection
from datetime import datetime

def hash_password(password):
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def register_user(email, password, name, phone, address):
    # Check for existing active account
    existing = query_db(
        "SELECT * FROM users WHERE email = ? AND deleted_at IS NULL",
        [email], one=True
    )
    if existing:
        return None, "Email already registered"

    # FIX: check for soft-deleted account with same email
    deleted_user = query_db(
        "SELECT * FROM users WHERE email = ? AND deleted_at IS NOT NULL",
        [email], one=True
    )

    hashed_password = hash_password(password)
    conn = get_db_connection()

    try:
        if deleted_user:
            # Check if still within 30-day restore window
            restore_by_str = deleted_user['restore_by']
            restore_by     = None
            for fmt in ('%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S'):
                try:
                    restore_by = datetime.strptime(restore_by_str, fmt)
                    break
                except (ValueError, TypeError):
                    continue

            if restore_by and datetime.now() < restore_by:
                # Within 30 days - RESTORE account with new password
                conn.execute(
                    """UPDATE users SET password = ?, name = ?, phone = ?, address = ?,
                       deleted_at = NULL, restore_by = NULL WHERE user_id = ?""",
                    [hashed_password, name, phone, address, deleted_user['user_id']]
                )
                conn.commit()
                return deleted_user['user_id'], None
            else:
                # Past 30 days - permanently delete old data then create fresh account
                _hard_delete_user(conn, deleted_user['user_id'])

        # Create fresh account
        cursor = conn.execute(
            """INSERT INTO users (email, password, name, phone, address, role)
               VALUES (?, ?, ?, ?, ?, 'customer')""",
            [email, hashed_password, name, phone, address]
        )
        conn.commit()
        return cursor.lastrowid, None

    except Exception as e:
        return None, str(e)
    finally:
        conn.close()


def _hard_delete_user(conn, user_id):
    """Permanently delete a user and all their data."""
    orders = conn.execute(
        "SELECT order_id FROM orders WHERE user_id = ?", [user_id]
    ).fetchall()
    for order in orders:
        conn.execute("DELETE FROM order_items WHERE order_id = ?", [order['order_id']])
        conn.execute("DELETE FROM payments WHERE order_id = ?", [order['order_id']])
    conn.execute("DELETE FROM orders WHERE user_id = ?", [user_id])
    conn.execute("DELETE FROM messages WHERE email IN (SELECT email FROM users WHERE user_id = ?)", [user_id])
    conn.execute("DELETE FROM users WHERE user_id = ?", [user_id])
    conn.commit()


def login_user(email, password):
    # FIX: only allow login for non-deleted accounts
    user = query_db(
        "SELECT * FROM users WHERE email = ? AND deleted_at IS NULL",
        [email], one=True
    )

    if user and verify_password(password, user['password']):
        session['user_id']    = user['user_id']
        session['user_name']  = user['name']
        session['user_role']  = user['role']
        session['user_email'] = user['email']
        return True, None

    return False, "Invalid email or password"


def logout_user():
    session.clear()


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'warning')
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('user_role') != 'admin':
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('home_page'))
        return f(*args, **kwargs)
    return decorated_function