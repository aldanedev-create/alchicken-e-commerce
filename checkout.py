from flask import render_template, request, session, redirect, url_for, flash, jsonify
from includes.auth import login_required
from includes.db import query_db, get_db_connection
from includes.functions import calculate_order_total, is_within_working_hours, get_order_status_message
from config.config import Config
import os

@login_required
def checkout_page():
    if 'cart' not in session or len(session['cart']) == 0:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('products_page'))

    user = query_db("SELECT * FROM users WHERE user_id = ?", [session['user_id']], one=True)
    totals = calculate_order_total(session['cart'])

    return render_template('checkout.html',
                           cart=session['cart'],
                           totals=totals,
                           user=user,
                           payment_methods=Config.PAYMENT_METHODS)

@login_required
def process_checkout():
    if request.method != 'POST':
        return redirect(url_for('checkout_page'))

    if 'cart' not in session or len(session['cart']) == 0:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('products_page'))

    delivery_option  = request.form.get('delivery_option')
    contact_number   = request.form.get('contact_number', '').strip()
    delivery_address = request.form.get('delivery_address', '').strip() if delivery_option == 'delivery' else None
    payment_method   = request.form.get('payment_method')

    if delivery_option not in ['delivery', 'pickup']:
        flash('Invalid delivery option', 'danger')
        return redirect(url_for('checkout_page'))

    if not contact_number:
        flash('Contact number is required', 'danger')
        return redirect(url_for('checkout_page'))

    if delivery_option == 'delivery' and not delivery_address:
        flash('Delivery address is required for delivery orders', 'danger')
        return redirect(url_for('checkout_page'))

    if not payment_method or payment_method not in Config.PAYMENT_METHODS:
        flash('Please select a payment method', 'danger')
        return redirect(url_for('checkout_page'))

    if payment_method.startswith('bank_transfer'):
        if 'payment_proof' not in request.files or request.files['payment_proof'].filename == '':
            flash('Payment proof is required for bank transfers', 'danger')
            return redirect(url_for('checkout_page'))

    totals = calculate_order_total(session['cart'], delivery_option)
    processing_message = get_order_status_message(None) if not is_within_working_hours() else "Your order is being processed."

    conn = get_db_connection()
    try:
        conn.execute("BEGIN TRANSACTION")

        cursor = conn.execute(
            """INSERT INTO orders (user_id, total_amount, tax_amount, delivery_option,
               delivery_address, contact_number, order_status, processing_message)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            [session['user_id'], totals['total'], totals['tax'], delivery_option,
             delivery_address, contact_number, 'pending', processing_message]
        )
        order_id = cursor.lastrowid

        for item in session['cart']:
            conn.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, item_price) VALUES (?, ?, ?, ?)",
                [order_id, item['product_id'], item['quantity'], item['price']]
            )
            conn.execute(
                "UPDATE products SET stock = stock - ? WHERE product_id = ?",
                [item['quantity'], item['product_id']]
            )

        conn.execute(
            "INSERT INTO payments (order_id, payment_method, payment_status) VALUES (?, ?, ?)",
            [order_id, payment_method, 'pending']
        )

        conn.execute("COMMIT")

        if payment_method.startswith('bank_transfer') and 'payment_proof' in request.files:
            file = request.files['payment_proof']
            if file and file.filename:
                from includes.functions import validate_file_upload
                filename, error = validate_file_upload(file, {'jpg', 'jpeg', 'png', 'pdf'})
                if filename and not error:
                    upload_path = Config.PAYMENT_PROOF_DIR
                    os.makedirs(upload_path, exist_ok=True)
                    file.save(os.path.join(upload_path, filename))
                    conn2 = get_db_connection()
                    conn2.execute(
                        "UPDATE payments SET payment_proof_file = ? WHERE order_id = ?",
                        [filename, order_id]
                    )
                    conn2.commit()
                    conn2.close()
            flash('Bank transfer received. We will verify your payment shortly.', 'info')

        session.pop('cart', None)
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_confirmation_page', order_id=order_id))

    except Exception as e:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
        flash(f'Error processing order: {str(e)}', 'danger')
        return redirect(url_for('checkout_page'))
    finally:
        conn.close()


@login_required
def save_customer_note(order_id):
    """POST /order/<order_id>/note — customer saves a note on their order."""
    order = query_db(
        "SELECT * FROM orders WHERE order_id = ? AND user_id = ?",
        [order_id, session['user_id']], one=True
    )

    if not order:
        return jsonify({'success': False, 'error': 'Order not found'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data received'}), 400

    note = data.get('note', '').strip()

    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE orders SET customer_note = ? WHERE order_id = ?",
            [note, order_id]
        )
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()