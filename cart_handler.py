from includes.db import query_db
from includes.functions import calculate_order_total
from flask import request, session, jsonify

def cart_handler():
    session.permanent = True
    if request.method != 'POST':
        return jsonify({'error': 'Method not allowed'}), 405

    data   = request.get_json()
    action = data.get('action') if data else None

    if action == 'add':
        product_id = data.get('product_id')
        quantity   = int(data.get('quantity', 1))

        product = query_db("SELECT * FROM products WHERE product_id = ?", [product_id], one=True)
        if not product:
            return jsonify({'error': 'Product not found'}), 404

        if 'cart' not in session:
            session['cart'] = []

        # Check total already in cart + new quantity against real stock
        current_qty = 0
        for item in session['cart']:
            if item['product_id'] == product_id:
                current_qty = item['quantity']
                break

        # Enforce stock cap server-side
        if current_qty + quantity > product['stock']:
            can_add = product['stock'] - current_qty
            if can_add <= 0:
                return jsonify({'error': f'You already have all {product["stock"]} in your cart'}), 400
            quantity = can_add

        # Always merge — never duplicate
        existing_item = next((i for i in session['cart'] if i['product_id'] == product_id), None)

        if existing_item:
            new_qty = existing_item['quantity'] + quantity
            if new_qty > product['stock']:
                new_qty = product['stock']
            existing_item['quantity']  = new_qty
            existing_item['max_stock'] = product['stock']
        else:
            session['cart'].append({
                'product_id': product['product_id'],
                'name':       product['name'],
                'price':      product['price'],
                'quantity':   quantity,
                'image_url':  product['image_url'],
                'max_stock':  product['stock']
            })

        session.modified = True
        cart_count = sum(i['quantity'] for i in session['cart'])
        return jsonify({'success': True, 'cart_count': cart_count})

    elif action == 'update':
        product_id = data.get('product_id')
        quantity   = int(data.get('quantity', 1))

        for item in session.get('cart', []):
            if item['product_id'] == product_id:
                if quantity <= 0:
                    session['cart'].remove(item)
                else:
                    if quantity > item['max_stock']:
                        return jsonify({'error': f'Only {item["max_stock"]} in stock'}), 400
                    item['quantity'] = quantity
                break

        session.modified = True
        totals = calculate_order_total(session.get('cart', []), 'pickup')
        return jsonify({'success': True, 'totals': totals})

    elif action == 'remove':
        product_id      = data.get('product_id')
        session['cart'] = [i for i in session.get('cart', []) if i['product_id'] != product_id]
        session.modified = True
        return jsonify({'success': True})

    elif action == 'clear':
        session['cart']  = []
        session.modified = True
        return jsonify({'success': True})

    elif action == 'get':
        cart = session.get('cart', [])

        # Deduplicate server-side (safety net)
        merged = {}
        for item in cart:
            pid = item['product_id']
            if pid not in merged:
                merged[pid] = dict(item)
            else:
                merged[pid]['quantity'] = min(
                    merged[pid]['quantity'] + item['quantity'],
                    item.get('max_stock', item['quantity'])
                )
        cart             = list(merged.values())
        session['cart']  = cart
        session.modified = True

        totals     = calculate_order_total(cart, 'pickup') if cart else None
        cart_count = sum(i['quantity'] for i in cart)
        return jsonify({'cart': cart, 'totals': totals, 'cart_count': cart_count})

    return jsonify({'error': 'Unknown action'}), 400