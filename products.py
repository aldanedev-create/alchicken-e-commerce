from flask import render_template, jsonify
from includes.db import query_db

def products_page():
    products = query_db("SELECT * FROM products WHERE stock > 0 ORDER BY product_id DESC")
    return render_template('products.html', products=products)

def get_products_api():
    products = query_db("SELECT product_id, name, description, price, stock, image_url FROM products WHERE stock > 0")
    return jsonify([dict(product) for product in products])