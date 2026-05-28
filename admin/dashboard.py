from flask import render_template
from includes.auth import admin_required
from includes.db import query_db
from datetime import datetime, timedelta

@admin_required
def admin_dashboard():
    # Get statistics
    total_orders = query_db("SELECT COUNT(*) as count FROM orders", one=True)['count']
    pending_orders = query_db("SELECT COUNT(*) as count FROM orders WHERE order_status = 'pending'", one=True)['count']
    total_products = query_db("SELECT COUNT(*) as count FROM products", one=True)['count']
    low_stock = query_db("SELECT COUNT(*) as count FROM products WHERE stock < 10", one=True)['count']
    
    today = datetime.now().strftime('%Y-%m-%d')
    today_orders = query_db("SELECT COUNT(*) as count FROM orders WHERE date(order_date) = ?", [today], one=True)['count']
    
    recent_orders = query_db(
        """SELECT o.*, u.name as customer_name 
           FROM orders o 
           JOIN users u ON o.user_id = u.user_id 
           ORDER BY o.order_date DESC LIMIT 5"""
    )
    
    recent_messages = query_db(
        "SELECT * FROM messages ORDER BY message_date DESC LIMIT 5"
    )
    
    stats = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_products': total_products,
        'low_stock': low_stock,
        'today_orders': today_orders
    }
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_orders=recent_orders,
                         recent_messages=recent_messages)