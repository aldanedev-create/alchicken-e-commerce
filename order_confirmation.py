from flask import render_template, request, session, redirect, url_for, flash
from includes.db import query_db
from includes.auth import login_required
from includes.functions import get_order_status_message

@login_required
def order_confirmation_page():
    order_id = request.args.get('order_id')
    
    if not order_id:
        flash('Order ID not provided', 'error')
        return redirect(url_for('products_page'))
    
    order = query_db(
        """SELECT o.*, u.name, u.email 
           FROM orders o 
           JOIN users u ON o.user_id = u.user_id 
           WHERE o.order_id = ? AND o.user_id = ?""",
        [order_id, session['user_id']], one=True
    )
    
    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('products_page'))
    
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
    
    processing_message = get_order_status_message(order['order_date'])
    
    return render_template('order_confirmation.html',
                         order=order,
                         items=order_items,
                         payment=payment,
                         processing_message=processing_message)