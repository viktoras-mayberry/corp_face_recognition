from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, current_user
from app.auth import bp
from app.models import User
from app import db

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = bool(request.form.get('remember'))
        
        if not email or not password:
            flash('Please provide both email and password.', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Contact administrator.', 'error')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.dashboard')
            return redirect(next_page)
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # Get form data
        state_code = request.form.get('state_code', '').strip().upper()
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        pin = request.form.get('pin', '').strip()
        
        # Validation
        errors = []
        
        if not state_code or len(state_code) < 6:
            errors.append('State code is required and must be at least 6 characters.')
        
        if not full_name or len(full_name) < 2:
            errors.append('Full name is required and must be at least 2 characters.')
        
        if not email or '@' not in email:
            errors.append('Valid email address is required.')
        
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if not pin or len(pin) != 4 or not pin.isdigit():
            errors.append('PIN must be exactly 4 digits.')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            errors.append('Email address already registered.')
        
        if User.query.filter_by(state_code=state_code).first():
            errors.append('State code already registered.')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('auth/register.html')
        
        # Create new user
        user = User(
            state_code=state_code,
            full_name=full_name,
            email=email,
            is_active=True  # Auto-activate for now, can be changed to require email verification
        )
        user.set_password(password)
        user.set_pin(pin)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/verify_pin', methods=['POST'])
def verify_pin():
    """Verify user PIN for sensitive operations"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    pin = request.form.get('pin', '').strip()
    
    if current_user.check_pin(pin):
        session['pin_verified'] = True
        flash('PIN verified successfully.', 'success')
        return redirect(request.args.get('next', url_for('main.dashboard')))
    else:
        flash('Invalid PIN. Please try again.', 'error')
        return redirect(request.args.get('next', url_for('main.dashboard')))
