from flask import render_template, request, redirect, url_for, flash
from includes.auth import register_user
from includes.functions import validate_email, validate_jamaica_phone

def register_page():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        phone = request.form.get('phone')
        address = request.form.get('address')
        
        # Validation
        if not all([name, email, password, confirm_password]):
            flash('All fields are required', 'danger')
            return render_template('register.html')
        
        if not validate_email(email):
            flash('Invalid email address', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return render_template('register.html')
        
        if phone and not validate_jamaica_phone(phone):
            flash('Invalid Jamaica phone number format. Use 876-XXX-XXXX', 'warning')
        
        user_id, error = register_user(email, password, name, phone, address)
        
        if user_id:
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login_page'))
        else:
            flash(error, 'danger')
    
    return render_template('register.html')