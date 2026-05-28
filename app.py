from flask import Flask, session, send_from_directory, abort, request, jsonify, make_response
from config.config import DevelopmentConfig, ProductionConfig
from datetime import timedelta
import os

app = Flask(__name__)

# Load configuration
if os.environ.get('FLASK_ENV') == 'production':
    app.config.from_object(ProductionConfig)
else:
    app.config.from_object(DevelopmentConfig)


# Ensure session cookies behave correctly
app.config.update(
    PERMANENT_SESSION_LIFETIME=timedelta(days=365),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,   # change to True in production
    SESSION_COOKIE_SAMESITE='Lax'
)

# ── Public route imports ───────────────────────────────────────────────────────
from index import home_page
from about import about_page
from products import products_page, get_products_api
from cart import cart_page
from cart_handler import cart_handler
from checkout import checkout_page, process_checkout, save_customer_note
from login import login_page
from register import register_page
from account import account_page
from contact import contact_page, save_contact_message
from logout import logout_page
from order_confirmation import order_confirmation_page
from order_status import order_tracking_page, track_order
from forgot_password import forgot_password_page, reset_password_page
from two_fa import two_fa_verify_page, two_fa_resend, two_fa_settings

# ── Admin route imports ────────────────────────────────────────────────────────
from admin.dashboard import admin_dashboard
from admin.manage_products import manage_products, add_product, edit_product, delete_product, update_stock
from admin.manage_orders import manage_orders, view_order_details, update_order_status, save_admin_note
from admin.manage_customers import manage_customers, delete_customer
from admin.backup import (admin_backup_page, admin_create_backup, admin_restore_backup,
                           admin_download_backup, admin_delete_backup, admin_export_csv)

# ── Public routes ──────────────────────────────────────────────────────────────
app.add_url_rule('/',                          'home_page',               home_page,               methods=['GET'])
app.add_url_rule('/about',                     'about_page',              about_page,              methods=['GET'])
app.add_url_rule('/products',                  'products_page',           products_page,           methods=['GET'])
app.add_url_rule('/api/products',              'get_products_api',        get_products_api,        methods=['GET'])
app.add_url_rule('/cart',                      'cart_page',               cart_page,               methods=['GET'])
app.add_url_rule('/api/cart',                  'cart_handler',            cart_handler,            methods=['POST'])
app.add_url_rule('/checkout',                  'checkout_page',           checkout_page,           methods=['GET', 'POST'])
app.add_url_rule('/process-checkout',          'process_checkout',        process_checkout,        methods=['POST'])
app.add_url_rule('/order/<int:order_id>/note', 'save_customer_note',      save_customer_note,      methods=['POST'])
app.add_url_rule('/login',                     'login_page',              login_page,              methods=['GET', 'POST'])
app.add_url_rule('/register',                  'register_page',           register_page,           methods=['GET', 'POST'])
app.add_url_rule('/account',                   'account_page',            account_page,            methods=['GET', 'POST'])
app.add_url_rule('/contact',                   'contact_page',            contact_page,            methods=['GET'])
app.add_url_rule('/contact/save',              'save_contact_message',    save_contact_message,    methods=['POST'])
app.add_url_rule('/logout',                    'logout_page',             logout_page,             methods=['GET'])
app.add_url_rule('/order-confirmation',        'order_confirmation_page', order_confirmation_page, methods=['GET'])
app.add_url_rule('/track-order',               'order_tracking_page',     order_tracking_page,     methods=['GET', 'POST'])
app.add_url_rule('/track',                     'track_order',             track_order,             methods=['POST'])
app.add_url_rule('/forgot-password',           'forgot_password_page',    forgot_password_page,    methods=['GET', 'POST'])
app.add_url_rule('/reset-password/<token>',    'reset_password_page',     reset_password_page,     methods=['GET', 'POST'])
app.add_url_rule('/two-fa/verify',              'two_fa_verify_page',      two_fa_verify_page,      methods=['GET', 'POST'])
app.add_url_rule('/two-fa/resend',               'two_fa_resend',           two_fa_resend,           methods=['POST'])
app.add_url_rule('/account/two-fa',              'two_fa_settings',         two_fa_settings,         methods=['POST'])

# ── Admin routes ───────────────────────────────────────────────────────────────
app.add_url_rule('/admin/dashboard',                               'admin_dashboard',     admin_dashboard,     methods=['GET'])
app.add_url_rule('/admin/products',                                'manage_products',     manage_products,     methods=['GET'])
app.add_url_rule('/admin/products/add',                            'add_product',         add_product,         methods=['GET', 'POST'])
app.add_url_rule('/admin/products/edit/<int:product_id>',          'edit_product',        edit_product,        methods=['GET', 'POST'])
app.add_url_rule('/admin/products/delete/<int:product_id>',        'delete_product',      delete_product,      methods=['POST'])
app.add_url_rule('/admin/products/update-stock/<int:product_id>',  'update_stock',        update_stock,        methods=['POST'])
app.add_url_rule('/admin/orders',                                  'manage_orders',       manage_orders,       methods=['GET'])
app.add_url_rule('/admin/orders/<int:order_id>',                   'view_order_details',  view_order_details,  methods=['GET'])
app.add_url_rule('/admin/orders/update/<int:order_id>',            'update_order_status', update_order_status, methods=['POST'])
app.add_url_rule('/admin/orders/<int:order_id>/note',              'save_admin_note',     save_admin_note,     methods=['POST'])
app.add_url_rule('/admin/customers',                               'manage_customers',    manage_customers,    methods=['GET'])
app.add_url_rule('/admin/customers/delete/<int:user_id>',          'delete_customer',     delete_customer,     methods=['POST'])
# Backup & Export routes
app.add_url_rule('/admin/backup',                                  'admin_backup_page',     admin_backup_page,     methods=['GET'])
app.add_url_rule('/admin/backup/create',                           'admin_create_backup',   admin_create_backup,   methods=['POST'])
app.add_url_rule('/admin/backup/restore',                           'admin_restore_backup',  admin_restore_backup,  methods=['POST'])
app.add_url_rule('/admin/backup/download/<filename>',               'admin_download_backup', admin_download_backup, methods=['GET'])
app.add_url_rule('/admin/backup/delete/<filename>',                 'admin_delete_backup',   admin_delete_backup,   methods=['POST'])
app.add_url_rule('/admin/export/<type>',                            'admin_export_csv',      admin_export_csv,      methods=['GET'])

# ── Payment proof file serving (admin only) ────────────────────────────────────
@app.route('/admin/payment-proof/<filename>')
def serve_payment_proof(filename):
    if session.get('user_role') != 'admin':
        abort(403)
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), 'uploads', 'payment_proofs'),
        filename
    )

# ── Context processor ──────────────────────────────────────────────────────────
@app.context_processor
def utility_processor():
    def get_cart_count():
        if 'cart' in session:
            return sum(item['quantity'] for item in session['cart'])
        return 0
    return dict(get_cart_count=get_cart_count)

# ── DB init helper ─────────────────────────────────────────────────────────────
@app.cli.command('init-db')
def init_db_command():
    """Create database tables. Run: flask init-db"""
    from includes.db import init_db
    init_db()
    print('Database initialised.')


@app.route('/set-cart-cookie', methods=['POST'])
def set_cart_cookie():
    data = request.get_json(silent=True) or {}
    cart_id = data.get('cart_id', 'guest')

    resp = make_response(jsonify({'success': True}))
    resp.set_cookie(
        'cart_id',
        cart_id,
        max_age=60*60*24*30,
        httponly=True,
        samesite='Lax'
    )
    return resp


@app.route('/get-cart-cookie')
def get_cart_cookie():
    return jsonify({'cart_id': request.cookies.get('cart_id')})


@app.route('/delete-cart-cookie', methods=['POST'])
def delete_cart_cookie():
    resp = make_response(jsonify({'success': True}))
    resp.delete_cookie('cart_id')
    return resp




if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)