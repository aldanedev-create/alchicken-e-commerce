import os
from dotenv import load_dotenv
from datetime import datetime


load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'alchicken-secret-key-2024-change-in-production'
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sql', 'alchicken.db')

    # FIX: was pointing to 'uploads/' but all templates load images from
    # 'static/images/products/' via url_for('static', ...).
    # Changed to static/images so saved images are actually served by Flask.
    STATIC_FOLDER    = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
    UPLOAD_FOLDER    = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images')
    PRODUCT_IMG_DIR  = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'images', 'products')
    PAYMENT_PROOF_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads', 'payment_proofs')

    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}   # removed pdf from image uploads
    ALLOWED_PROOF_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'adminalchicken@gmail.com'
    BUSINESS_NAME = 'ALChicken'
    BUSINESS_ADDRESS = 'Kingston, Jamaica'

   

    DELIVERY_FEE = 500
    DELIVERY_AREA = 'Kingston Metropolitan Area'
    GCT_RATE = 0.15

    PAYMENT_METHODS = [
        'bank_transfer_ncb',
        'bank_transfer_scotiabank',
        'bank_transfer_jmmb',
        'paypal',
        'cash_on_delivery'
    ]

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'

    DEBUG = False
    TESTING = False

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


def get_operating_hours():
    day = datetime.now().weekday()  # 0=Monday, 6=Sunday
    if day == 6:                    # Sunday
        return '9:00 AM - 4:00 PM'
    elif day == 5:                  # Saturday
        return '9:00 AM - 4:00 PM'
    else:                           # Monday - Friday
        return '9:00 AM - 6:00 PM'