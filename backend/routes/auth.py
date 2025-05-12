from flask import Blueprint, render_template, redirect, request, url_for, flash
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from ..utils.logger import logger
from ..models.user import User
from datetime import datetime
from ..instances import db


auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        address = request.form['address']
        city = request.form['city']
        phone_number = request.form['phone_number']
        date_of_birth_str = request.form['date_of_birth']
        email = request.form['email']
        password = request.form['password']

        # Check all fields
        if not all([first_name, last_name, address, city, phone_number, date_of_birth_str, email, password]):
            flash("Please fill in all fields to register a new account!", 'warning')
            return redirect(url_for('auth.register'))

        # Validate date
        try:
            date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", 'warning')
            return redirect(url_for('auth.register'))

        # Check if user exists
        check_user = User.query.filter_by(email=email).first()
        if check_user:
            flash("A User with that email already exists, please login!", 'warning')
            return redirect(url_for('auth.register'))

        try:
            new_user = User(
                first_name=first_name,
                last_name=last_name,
                address=address,
                city=city,
                phone_number=phone_number,
                date_of_birth=date_of_birth,  # Now correct type
                email=email,
                password_hash=generate_password_hash(password)
            )
            
            db.session.add(new_user)
            db.session.commit()
            flash('Registration Successful!', 'success')
            login(new_user)
            return redirect(url_for('user.dashboard'))

        except Exception as e:
            flash("Something went wrong while registering the account!", "error")
            logger.error(f"Error in user registration: {e}")
            return redirect(url_for('main.home'))
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        if not email or not password:
            flash("Please fill in all fields to login!", 'warning')
        
        check_user = User.query.filter_by(email=email).first()

        if not check_user:
            flash("No user found with that email, please register an account!", 'warning')
        
        if not check_password_hash(check_user.password_hash, password):
            flash("Invalid password, please try again.", 'warning')
        
        else:
            try:
                login_user(check_user)
                flash("Login Successful!", 'success')
                return redirect(url_for('user.dashboard'))
            except Exception as e:
                flash("Something went wrong during login, please try again!", 'error')
                logger.error(f'Error during Login: {e}')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout', methods=['POST'])
def logout():
    logout_user()
    flash("Logout Successful", 'success')
    return redirect(url_for('auth.login'))
        
