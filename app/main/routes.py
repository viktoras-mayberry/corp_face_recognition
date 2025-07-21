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
    ).order_by(Attendance.created_at.desc()).limit(5).all()
    
    # Get active announcements
    from app.models import Announcement
    announcements = Announcement.get_active_announcements()[:5]  # Latest 5 announcements
    
    # Get user attendance statistics
    attendance_stats = current_user.get_attendance_summary()
    
    return render_template('dashboard.html', 
                         schedules=today_schedules, 
                         recent_attendance=recent_attendance,
                         announcements=announcements,
                         attendance_stats=attendance_stats)

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
    ).order_by(Attendance.created_at.desc()).paginate(
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

@bp.route('/face_attendance')
@login_required
def face_attendance():
    """Face recognition attendance page"""
    # Get today's active schedules
    today_schedules = CDSchedule.query.filter_by(
        schedule_date=date.today(),
        is_active=True
    ).all()
    
    return render_template('face_attendance.html', schedules=today_schedules)

@bp.route('/mark_face_attendance', methods=['POST'])
@login_required
def mark_face_attendance():
    """Mark attendance using face recognition and PIN"""
    try:
        data = request.get_json()
        schedule_id = data.get('schedule_id')
        pin = data.get('pin')
        
        if not schedule_id or not pin:
            return jsonify({'error': 'Schedule ID and PIN are required'}), 400
        
        # Use the attendance service to mark attendance
        from app.services.attendance_service import AttendanceService
        attendance_service = AttendanceService()
        
        # Get location from schedule
        schedule = CDSchedule.query.get(schedule_id)
        if not schedule:
            return jsonify({'error': 'Invalid schedule'}), 404
        
        result = attendance_service.mark_attendance_by_face_and_pin(
            current_user.state_code, pin, schedule.location_id
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': result['message'],
                'user_name': result.get('user_name', current_user.full_name),
                'check_in_time': result.get('check_in_time')
            })
        else:
            return jsonify({'error': result['message']}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error in face attendance: {str(e)}")
        return jsonify({'error': 'System error occurred'}), 500

@bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    return render_template('errors/500.html'), 500
