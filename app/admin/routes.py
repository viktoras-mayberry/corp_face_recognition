from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.admin import bp
from app.models import User, Attendance, Location, CDSchedule
from app import db
from datetime import date, datetime

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_locations = Location.query.count()
    today_attendance = Attendance.query.filter(
        Attendance.timestamp >= datetime.combine(date.today(), datetime.min.time())
    ).count()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         total_locations=total_locations,
                         today_attendance=today_attendance)

@bp.route('/users')
@login_required
@admin_required
def users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/users.html', users=users)

@bp.route('/users/<int:user_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Toggle user active status"""
    user = User.query.get_or_404(user_id)
    user.is_active = not user.is_active
    db.session.commit()
    
    status = "activated" if user.is_active else "deactivated"
    flash(f'User {user.full_name} has been {status}.', 'success')
    return redirect(url_for('admin.users'))

@bp.route('/locations')
@login_required
@admin_required
def locations():
    """Manage locations"""
    locations = Location.query.order_by(Location.name).all()
    return render_template('admin/locations.html', locations=locations)

@bp.route('/schedules')
@login_required
@admin_required
def schedules():
    """Manage CD schedules"""
    schedules = CDSchedule.query.order_by(CDSchedule.schedule_date.desc()).all()
    return render_template('admin/schedules.html', schedules=schedules)

@bp.route('/attendance')
@login_required
@admin_required
def attendance():
    """View all attendance records"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    attendance_records = Attendance.query.order_by(Attendance.timestamp.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/attendance.html', attendance_records=attendance_records)

@bp.route('/reports')
@login_required
@admin_required
def reports():
    """Generate reports"""
    return render_template('admin/reports.html')
