from flask import render_template, request, redirect, url_for, flash
from includes.db import get_db_connection, query_db
from includes.auth import admin_required

@admin_required
def manage_customers():
    customers_raw = query_db(
        "SELECT * FROM users WHERE role = 'customer' ORDER BY created_at DESC"
    )

    # FIX: sqlite3.Row objects are read-only; convert to dicts so we can add extra keys
    customers = []
    for row in customers_raw:
        customer = dict(row)

        order_count = query_db(
            "SELECT COUNT(*) as count FROM orders WHERE user_id = ?",
            [customer['user_id']], one=True
        )
        customer['order_count'] = order_count['count'] if order_count else 0

        total_spent = query_db(
            "SELECT SUM(total_amount) as total FROM orders WHERE user_id = ?",
            [customer['user_id']], one=True
        )
        customer['total_spent'] = total_spent['total'] or 0 if total_spent else 0

        customers.append(customer)

    return render_template('admin/manage_customers.html', customers=customers)



@admin_required
def delete_customer(user_id):
    if request.method == 'POST':
        conn = get_db_connection()
        try:
            conn.execute("BEGIN TRANSACTION")

            orders = conn.execute(
                "SELECT order_id FROM orders WHERE user_id = ?", [user_id]
            ).fetchall()

            for order in orders:
                conn.execute("DELETE FROM order_items WHERE order_id = ?", [order['order_id']])
                conn.execute("DELETE FROM payments WHERE order_id = ?", [order['order_id']])

            conn.execute("DELETE FROM orders WHERE user_id = ?", [user_id])
            conn.execute(
                "DELETE FROM messages WHERE email IN (SELECT email FROM users WHERE user_id = ?)",
                [user_id]
            )
            conn.execute("DELETE FROM users WHERE user_id = ?", [user_id])
            conn.execute("COMMIT")
            flash('Customer account deleted successfully', 'success')

        except Exception as e:
            conn.execute("ROLLBACK")
            flash(f'Error deleting customer: {str(e)}', 'danger')
        finally:
            conn.close()

    return redirect(url_for('manage_customers'))
