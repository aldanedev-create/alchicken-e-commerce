from flask import render_template, request, flash, session, redirect, url_for
from includes.db import query_db
from includes.functions import sanitize_input
from includes.auth import login_required
from datetime import datetime


@login_required
def order_tracking_page():
    return render_template('order_tracking.html')


@login_required
def track_order():
    if request.method == 'POST':
        order_number = sanitize_input(request.form.get('order_number', ''))
        email        = sanitize_input(request.form.get('email', ''))

        if not order_number or not email:
            flash('Please provide both order number and email.', 'danger')
            return render_template('order_tracking.html')

        # FIX: verify the email matches the logged-in user's email
        # This prevents a customer from looking up another customer's order
        # by guessing order numbers
        logged_in_email = session.get('user_email', '')
        if email.lower() != logged_in_email.lower():
            flash('Email does not match your account.', 'danger')
            return render_template('order_tracking.html')

        order = query_db(
            """SELECT o.*, u.name, u.email, u.phone,
                      p.payment_method, p.payment_status
               FROM orders o
               JOIN users u ON o.user_id = u.user_id
               LEFT JOIN payments p ON o.order_id = p.order_id
               WHERE o.order_id = ? AND u.email = ? AND o.user_id = ?""",
            [order_number, email, session['user_id']], one=True
        )

        if order:
            order       = dict(order)
            order_items = query_db(
                """SELECT oi.*, p.name, p.image_url
                   FROM order_items oi
                   JOIN products p ON oi.product_id = p.product_id
                   WHERE oi.order_id = ?""",
                [order_number]
            )

            status_timeline = generate_status_timeline(order)

            return render_template('order_status.html',
                                   order=order,
                                   items=order_items,
                                   timeline=status_timeline)
        else:
            flash('Order not found. Please check your order number and email.', 'danger')
            return render_template('order_tracking.html')

    return render_template('order_tracking.html')


# FIX: removed @login_required - this is a helper function, not a route
def generate_status_timeline(order):
    timeline = []

    # Order placed
    timeline.append({
        'status':      'Order Placed',
        'date':        order.get('order_date'),
        'completed':   True,
        'description': 'Your order has been received'
    })

    # Payment status
    payment_status = order.get('payment_status', 'pending')
    if payment_status == 'confirmed':
        timeline.append({
            'status':      'Payment Confirmed',
            'date':        order.get('payment_date'),
            'completed':   True,
            'description': 'Payment has been verified'
        })
    else:
        timeline.append({
            'status':      'Payment Confirmed',
            'date':        None,
            'completed':   False,
            'description': 'Awaiting payment confirmation'
        })

    # Order processing stages
    status_map = {
        'processing':         ('Order Processing',    'Your order is being prepared'),
        'ready_for_pickup':   ('Ready for Pickup',    'Your order is ready for pickup'),
        'ready_for_delivery': ('Ready for Delivery',  'Your order is ready for delivery'),
        'completed':          ('Completed',           'Order has been fulfilled')
    }

    order_status = order.get('order_status', 'pending')
    if order_status in status_map:
        status_text, description = status_map[order_status]
        timeline.append({
            'status':      status_text,
            'date':        None,
            'completed':   order_status != 'processing',
            'description': description
        })

    return timeline