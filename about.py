from flask import render_template

def about_page():
    return render_template('about.html',
                           farmer_name='Althea Hutchinson',
                           farming_years=20,
                           location='Kingston, Jamaica')
