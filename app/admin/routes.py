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
        Attendance.created_at >= datetime.combine(date.today(), datetime.min.time())
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

@bp.route('/locations/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_location():
    """Create new location"""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            address = request.form.get('address', '').strip()
            local_government = request.form.get('local_government', '').strip()
            state = request.form.get('state', '').strip()
            latitude = request.form.get('latitude', '').strip()
            longitude = request.form.get('longitude', '').strip()
            radius = request.form.get('radius', '').strip()
            capacity = request.form.get('capacity', '').strip()
            description = request.form.get('description', '').strip()
            is_active = request.form.get('active') == 'on'
            if not name or not address or not local_government or not state:
                flash('Name, address, local government, and state are required.', 'error')
                return render_template('admin/location_form.html', location=None)
            lat_val = float(latitude) if latitude else None
            lng_val = float(longitude) if longitude else None
            radius_val = int(radius) if radius else 100
            capacity_val = int(capacity) if capacity else None
            location = Location(
                name=name,
                address=address,
                local_government=local_government,
                state=state,
                latitude=lat_val,
                longitude=lng_val,
                radius=radius_val,
                max_capacity=capacity_val,
                description=description,
                is_active=is_active
            )
            db.session.add(location)
            db.session.commit()
            flash('Location created successfully!', 'success')
            return redirect(url_for('admin.locations'))
        except ValueError:
            flash('Invalid coordinates, radius, or capacity value.', 'error')
        except Exception as e:
            flash(f'Error creating location: {str(e)}', 'error')
    return render_template('admin/location_form.html', location=None)

@bp.route('/locations/<int:location_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_location(location_id):
    """Edit existing location (all fields)."""
    location = Location.query.get_or_404(location_id)
    if request.method == 'POST':
        try:
            location.name = request.form.get('name', '').strip()
            location.address = request.form.get('address', '').strip()
            location.local_government = request.form.get('local_government', '').strip()
            location.state = request.form.get('state', '').strip()
            latitude = request.form.get('latitude', '').strip()
            longitude = request.form.get('longitude', '').strip()
            radius = request.form.get('radius', '').strip()
            capacity = request.form.get('capacity', '').strip()
            description = request.form.get('description', '').strip()
            is_active = request.form.get('active') == 'on'
            if not location.name or not location.address or not location.local_government or not location.state:
                flash('Name, address, local government, and state are required.', 'error')
                return render_template('admin/location_form.html', location=location)
            location.latitude = float(latitude) if latitude else None
            location.longitude = float(longitude) if longitude else None
            location.radius = int(radius) if radius else 100
            location.max_capacity = int(capacity) if capacity else None
            location.description = description
            location.is_active = is_active
            db.session.commit()
            flash('Location updated successfully!', 'success')
            return redirect(url_for('admin.locations'))
        except ValueError:
            flash('Invalid coordinates, radius, or capacity value.', 'error')
        except Exception as e:
            flash(f'Error updating location: {str(e)}', 'error')
    return render_template('admin/location_form.html', location=location)

@bp.route('/locations/<int:location_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_location(location_id):
    """Delete location"""
    location = Location.query.get_or_404(location_id)
    
    try:
        # Check if location is being used in schedules
        from app.models import CDSchedule
        active_schedules = CDSchedule.query.filter_by(location_id=location_id, is_active=True).count()
        if active_schedules > 0:
            flash(f'Cannot delete location. It is being used in {active_schedules} active schedules.', 'error')
            return redirect(url_for('admin.locations'))
        
        db.session.delete(location)
        db.session.commit()
        flash('Location deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting location: {str(e)}', 'error')
    
    return redirect(url_for('admin.locations'))

@bp.route('/locations/<int:location_id>/toggle_status', methods=['POST'])
@login_required
@admin_required
def toggle_location_status(location_id):
    """Toggle location active status"""
    location = Location.query.get_or_404(location_id)
    location.is_active = not location.is_active
    db.session.commit()
    
    status = "activated" if location.is_active else "deactivated"
    flash(f'Location "{location.name}" has been {status}.', 'success')
    return redirect(url_for('admin.locations'))

@bp.route('/schedules')
@login_required
@admin_required
def schedules():
    """Manage CD schedules"""
    schedules = CDSchedule.query.order_by(CDSchedule.schedule_date.desc()).all()
    return render_template('admin/schedules.html', schedules=schedules)

@bp.route('/schedules/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_schedule():
    """Create new CD schedule. Require at least one active location."""
    locations = Location.query.filter_by(is_active=True).all()
    if not locations:
        flash('You must set up at least one active location before scheduling a meeting.', 'warning')
        return redirect(url_for('admin.locations'))
    if request.method == 'POST':
        try:
            schedule_date = datetime.strptime(request.form['schedule_date'], '%Y-%m-%d').date()
            start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
            end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
            schedule = CDSchedule(
                schedule_date=schedule_date,
                location_id=request.form['location_id'],
                activity_type=request.form['activity_type'],
                start_time=start_time,
                end_time=end_time,
                description=request.form.get('description', '').strip(),
                is_active=True
            )
            db.session.add(schedule)
            db.session.commit()
            flash('Schedule created successfully!', 'success')
            return redirect(url_for('admin.schedules'))
        except Exception as e:
            flash(f'Error creating schedule: {str(e)}', 'error')
    return render_template('admin/schedule_form.html', locations=locations, schedule=None)

@bp.route('/schedules/<int:schedule_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_schedule(schedule_id):
    """Edit existing schedule"""
    schedule = CDSchedule.query.get_or_404(schedule_id)
    
    if request.method == 'POST':
        try:
            schedule.schedule_date = datetime.strptime(request.form['schedule_date'], '%Y-%m-%d').date()
            schedule.start_time = datetime.strptime(request.form['start_time'], '%H:%M').time()
            schedule.end_time = datetime.strptime(request.form['end_time'], '%H:%M').time()
            schedule.location_id = request.form['location_id']
            schedule.activity_type = request.form['activity_type']
            schedule.description = request.form.get('description', '').strip()
            
            db.session.commit()
            
            flash('Schedule updated successfully!', 'success')
            return redirect(url_for('admin.schedules'))
            
        except Exception as e:
            flash(f'Error updating schedule: {str(e)}', 'error')
    
    locations = Location.query.filter_by(is_active=True).all()
    return render_template('admin/schedule_form.html', locations=locations, schedule=schedule)

@bp.route('/schedules/<int:schedule_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_schedule(schedule_id):
    """Delete schedule"""
    schedule = CDSchedule.query.get_or_404(schedule_id)
    
    try:
        db.session.delete(schedule)
        db.session.commit()
        flash('Schedule deleted successfully!', 'success')
    except Exception as e:
        flash(f'Error deleting schedule: {str(e)}', 'error')
    
    return redirect(url_for('admin.schedules'))

@bp.route('/attendance')
@login_required
@admin_required
def attendance():
    """View all attendance records"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    attendance_records = Attendance.query.order_by(Attendance.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/attendance.html', attendance_records=attendance_records)

@bp.route('/reports')
@login_required
@admin_required
def reports():
    """Generate reports"""
    return render_template('admin/reports.html')

@bp.route('/send_announcement', methods=['POST'])
@login_required
@admin_required
def send_announcement():
    """Send announcement to all corps members"""
    try:
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        announcement_type = request.form.get('type', 'info')
        
        if not title or not message:
            flash('Title and message are required.', 'error')
            return redirect(url_for('admin.dashboard'))
        
        # Create announcement
        from app.models import Announcement
        announcement = Announcement(
            title=title,
            message=message,
            announcement_type=announcement_type,
            is_active=True,
            is_urgent=(announcement_type in ['warning', 'danger']),
            created_by=current_user.id
        )
        
        db.session.add(announcement)
        db.session.commit()
        
        flash(f'Announcement "{title}" has been sent successfully!', 'success')
        return redirect(url_for('admin.dashboard'))
        
    except Exception as e:
        flash(f'Error sending announcement: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@bp.route('/announcements')
@login_required
@admin_required
def announcements():
    """Manage announcements"""
    from app.models import Announcement
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('admin/announcements.html', announcements=announcements)
