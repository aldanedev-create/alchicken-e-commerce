from flask import render_template, request, redirect, url_for, flash, session
from includes.db import get_db_connection, query_db
from includes.auth import admin_required
from includes.functions import get_order_status_message

@admin_required
def manage_orders():
    orders = query_db(
        """SELECT o.*, u.name as customer_name, u.email as customer_email,
                  p.payment_status
           FROM orders o 
           JOIN users u ON o.user_id = u.user_id 
           LEFT JOIN payments p ON o.order_id = p.order_id
           ORDER BY o.order_date DESC"""
    )
    
    return render_template('admin/manage_orders.html', orders=orders)

@admin_required
def view_order_details(order_id):
    order = query_db(
        """SELECT o.*, u.name as customer_name, u.email as customer_email, 
                  u.phone as customer_phone, u.address as customer_address
           FROM orders o 
           JOIN users u ON o.user_id = u.user_id 
           WHERE o.order_id = ?""",
        [order_id], one=True
    )
    
    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('manage_orders'))
    
    order_items = query_db(
        """SELECT oi.*, p.name, p.image_url 
           FROM order_items oi 
           JOIN products p ON oi.product_id = p.product_id 
           WHERE oi.order_id = ?""",
        [order_id]
    )
    
    payment = query_db(
        "SELECT * FROM payments WHERE order_id = ?",
        [order_id], one=True
    )
    
    return render_template('admin/order_details.html',
                         order=order,
                         items=order_items,
                         payment=payment)

@admin_required
def update_order_status(order_id):
    if request.method == 'POST':
        new_status = request.form.get('order_status')
        payment_status = request.form.get('payment_status')
        
        conn = get_db_connection()
        
        if new_status:
            conn.execute(
                "UPDATE orders SET order_status = ? WHERE order_id = ?",
                [new_status, order_id]
            )
        
        if payment_status:
            conn.execute(
                "UPDATE payments SET payment_status = ? WHERE order_id = ?",
                [payment_status, order_id]
            )
        
        conn.commit()
        conn.close()
        
        flash('Order status updated successfully', 'success')
    
    return redirect(url_for('view_order_details', order_id=order_id))

@admin_required
def save_admin_note(order_id):
    """POST /admin/orders/<order_id>/note — admin saves a note on an order."""
    from flask import jsonify
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data received'}), 400

    note = data.get('note', '').strip()

    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE orders SET note = ? WHERE order_id = ?",
            [note, order_id]
        )
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()