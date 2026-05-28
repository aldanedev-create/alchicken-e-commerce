from flask import redirect, url_for, flash
from includes.auth import logout_user

def logout_page():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('home_page'))