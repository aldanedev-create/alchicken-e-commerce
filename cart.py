from flask import render_template, session
from includes.functions import calculate_order_total

def cart_page():
    cart_items = session.get('cart', [])
    if cart_items:
        totals = calculate_order_total(cart_items, 'pickup')
    else:
        totals = {'subtotal': 0, 'tax': 0, 'delivery_fee': 0, 'total': 0}
    
    return render_template('cart.html', cart=cart_items, totals=totals)