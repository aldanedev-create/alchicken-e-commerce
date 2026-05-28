from flask import render_template
from includes.db import query_db
from datetime import datetime

def home_page():
    featured_products = query_db(
        "SELECT * FROM products WHERE stock > 0 ORDER BY product_id DESC LIMIT 4"
    )

    return render_template(
        'index.html',
        business_name='ALChicken',
        featured_products=featured_products,
        delivery_area='Kingston Metropolitan Area',
        operating_hours=get_operating_hours()  # ✅ Added this
    )

def get_operating_hours():
    day = datetime.now().weekday()  # 0=Monday, 6=Sunday

    if day == 6:  # Sunday
        return '9:00 AM - 4:00 PM'
    elif day == 5:  # Saturday
        return '9:00 AM - 4:00 PM'
    else:  # Monday - Friday
        return '9:00 AM - 6:00 PM'