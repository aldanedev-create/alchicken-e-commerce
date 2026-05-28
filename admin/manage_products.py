from flask import render_template, request, redirect, url_for, flash
from includes.db import get_db_connection, query_db
from includes.auth import admin_required
from includes.functions import validate_file_upload
from config.config import Config
import os

@admin_required
def manage_products():
    products = query_db("SELECT * FROM products ORDER BY product_id DESC")
    return render_template('admin/manage_products.html', products=products)

@admin_required
def add_product():
    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price_str   = request.form.get('price', '')
        stock_str   = request.form.get('stock', '0')

        if not name or not price_str:
            flash('Name and price are required', 'danger')
            return render_template('admin/add_product.html')

        try:
            price = float(price_str)
            stock = int(stock_str)
        except ValueError:
            flash('Invalid price or stock value', 'danger')
            return render_template('admin/add_product.html')

        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename, error = validate_file_upload(file, Config.ALLOWED_EXTENSIONS)
                if error:
                    flash(error, 'danger')
                    return render_template('admin/add_product.html')
                if filename:
                    # FIX: save to static/images/products/ so Flask can serve it
                    os.makedirs(Config.PRODUCT_IMG_DIR, exist_ok=True)
                    file.save(os.path.join(Config.PRODUCT_IMG_DIR, filename))
                    image_filename = filename

        conn = get_db_connection()
        conn.execute(
            "INSERT INTO products (name, description, price, stock, image_url) VALUES (?, ?, ?, ?, ?)",
            [name, description, price, stock, image_filename]
        )
        conn.commit()
        conn.close()

        flash('Product added successfully', 'success')
        return redirect(url_for('manage_products'))

    return render_template('admin/add_product.html')

@admin_required
def edit_product(product_id):
    product = query_db("SELECT * FROM products WHERE product_id = ?", [product_id], one=True)

    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('manage_products'))

    if request.method == 'POST':
        name        = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        price_str   = request.form.get('price', '')
        stock_str   = request.form.get('stock', '0')

        if not name or not price_str:
            flash('Name and price are required', 'danger')
            return render_template('admin/edit_product.html', product=product)

        try:
            price = float(price_str)
            stock = int(stock_str)
        except ValueError:
            flash('Invalid price or stock value', 'danger')
            return render_template('admin/edit_product.html', product=product)

        conn = get_db_connection()
        new_image_filename = None

        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename:
                filename, error = validate_file_upload(file, Config.ALLOWED_EXTENSIONS)
                if error:
                    flash(error, 'danger')
                    conn.close()
                    return render_template('admin/edit_product.html', product=product)
                if filename:
                    # Delete old image
                    if product['image_url']:
                        old_path = os.path.join(Config.PRODUCT_IMG_DIR, product['image_url'])
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    # FIX: save to static/images/products/
                    os.makedirs(Config.PRODUCT_IMG_DIR, exist_ok=True)
                    file.save(os.path.join(Config.PRODUCT_IMG_DIR, filename))
                    new_image_filename = filename

        if new_image_filename:
            conn.execute(
                "UPDATE products SET name=?, description=?, price=?, stock=?, image_url=? WHERE product_id=?",
                [name, description, price, stock, new_image_filename, product_id]
            )
        else:
            conn.execute(
                "UPDATE products SET name=?, description=?, price=?, stock=? WHERE product_id=?",
                [name, description, price, stock, product_id]
            )

        conn.commit()
        conn.close()
        flash('Product updated successfully', 'success')
        return redirect(url_for('manage_products'))

    return render_template('admin/edit_product.html', product=product)

@admin_required
def delete_product(product_id):
    if request.method == 'POST':
        product = query_db("SELECT * FROM products WHERE product_id = ?", [product_id], one=True)
        if product and product['image_url']:
            image_path = os.path.join(Config.PRODUCT_IMG_DIR, product['image_url'])
            if os.path.exists(image_path):
                os.remove(image_path)

        conn = get_db_connection()
        conn.execute("DELETE FROM products WHERE product_id = ?", [product_id])
        conn.commit()
        conn.close()
        flash('Product deleted successfully', 'success')

    return redirect(url_for('manage_products'))

@admin_required
def update_stock(product_id):
    if request.method == 'POST':
        try:
            stock = int(request.form.get('stock', 0))
            if stock < 0:
                flash('Stock cannot be negative', 'danger')
                return redirect(url_for('manage_products'))
            conn = get_db_connection()
            conn.execute("UPDATE products SET stock = ? WHERE product_id = ?", [stock, product_id])
            conn.commit()
            conn.close()
            flash('Stock updated successfully', 'success')
        except ValueError:
            flash('Invalid stock value', 'danger')

    return redirect(url_for('manage_products'))