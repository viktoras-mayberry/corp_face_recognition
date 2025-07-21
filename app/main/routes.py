from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from app.main import bp
from app.models import User, Attendance, Location, CDSchedule
from app.services.attendance_service import AttendanceService
from app import db
from datetime import date, datetime

@bp.route('/')
def index():
    """Home page - redirect to dashboard if logged in, otherwise show landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    # Get today's schedules
    today_schedules = CDSchedule.query.filter_by(
        schedule_date=date.today(),
        is_active=True
    ).all()
    
    # Get user's recent attendance
    recent_attendance = Attendance.query.filter_by(
        user_id=current_user.id
    ).order_by(Attendance.timestamp.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         schedules=today_schedules, 
                         recent_attendance=recent_attendance)

@bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    return render_template('profile.html', user=current_user)

@bp.route('/attendance')
@login_required
def attendance_history():
    """View attendance history"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    attendance_records = Attendance.query.filter_by(
        user_id=current_user.id
    ).order_by(Attendance.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('attendance_history.html', 
                         attendance_records=attendance_records)

@bp.route('/locations')
@login_required
def locations():
    """View available locations"""
    locations = Location.query.filter_by(is_active=True).all()
    return render_template('locations.html', locations=locations)

@bp.route('/schedule')
@login_required
def schedule():
    """View CD schedule"""
    # Get upcoming schedules
    upcoming_schedules = CDSchedule.query.filter(
        CDSchedule.schedule_date >= date.today(),
        CDSchedule.is_active == True
    ).order_by(CDSchedule.schedule_date).all()
    
    return render_template('schedule.html', schedules=upcoming_schedules)

@bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('errors/404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('errors/500.html'), 500
