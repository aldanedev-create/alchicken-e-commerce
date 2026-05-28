import re
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from config.config import Config

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_jamaica_phone(phone):
    # Accepts formats: 876-XXX-XXXX, 8761234567, (876) 123-4567, etc.
    pattern = r'^\(?876\)?[-.\s]?\d{3}[-.\s]?\d{4}$|^\(?658\)?[-.\s]?\d{3}[-.\s]?\d{4}$'
    return re.match(pattern, phone) is not None

def calculate_gct(amount):
    return round(amount * Config.GCT_RATE, 2)

def calculate_order_total(cart_items, delivery_option='pickup'):
    subtotal = sum(item['price'] * item['quantity'] for item in cart_items)
    tax = calculate_gct(subtotal)
    delivery_fee = Config.DELIVERY_FEE if delivery_option == 'delivery' else 0

    return {
        'subtotal': round(subtotal, 2),
        'tax': tax,
        'delivery_fee': delivery_fee,
        'total': round(subtotal + tax + delivery_fee, 2)
    }

def validate_file_upload(file, allowed_extensions=None):
    if allowed_extensions is None:
        allowed_extensions = Config.ALLOWED_EXTENSIONS

    if not file or file.filename == '':
        return None, 'No file selected'

    if '.' not in file.filename:
        return None, 'Invalid file extension'

    ext = file.filename.rsplit('.', 1)[1].lower()
    if ext not in allowed_extensions:
        return None, f'File type not allowed. Allowed: {", ".join(allowed_extensions)}'

    # FIX: seek to end to get size WITHOUT consuming the stream for saving
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)

    if file_size > Config.MAX_FILE_SIZE:
        return None, f'File too large. Maximum {Config.MAX_FILE_SIZE // (1024 * 1024)}MB'

    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_filename = f"{timestamp}_{filename}"

    return unique_filename, None

def sanitize_input(input_string):
    if not input_string:
        return ''
    return input_string.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')

def get_current_time():
    return datetime.now()

def is_within_working_hours():
    now = datetime.now()
    # Mon-Fri 9am-6pm, Sat 9am-4pm, Sun closed
    weekday = now.weekday()  # 0=Mon, 6=Sun
    if weekday == 6:
        return False
    if weekday == 5:
        return 9 <= now.hour < 16
    return 9 <= now.hour < 18

def get_order_status_message(order_time):
    """Return a human-readable message based on when the order was placed."""
    if isinstance(order_time, str):
        # Try full datetime string first, then date only
        for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d'):
            try:
                order_time = datetime.strptime(order_time, fmt)
                break
            except ValueError:
                continue

    if isinstance(order_time, datetime):
        if not is_within_working_hours():
            return "Your order was received and will be processed next business day (Mon–Fri 9am–6pm, Sat 9am–4pm)."
        return "Your order has been received and is being processed today."

    return "Your order has been received."
