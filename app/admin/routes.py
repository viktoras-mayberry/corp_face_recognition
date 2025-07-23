from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app.admin import bp
from app.models import User, Attendance, Location, CDSchedule
from app import db
from datetime import date, datetime, timedelta
from sqlalchemy import or_, and_
import csv
from flask import Response

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def root_redirect():
    """Redirect admin root to attendance records page instead of dashboard."""
    return redirect(url_for('admin.attendance'))

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
    location_map_data = [
        {'name': loc.name, 'latitude': loc.latitude, 'longitude': loc.longitude}
        for loc in locations if loc.latitude is not None and loc.longitude is not None
    ]
    return render_template('admin/locations.html', locations=locations, location_map_data=location_map_data)

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
    """View all attendance records with robust filtering and search and real-time analytics"""
    from sqlalchemy import or_, and_, func
    from datetime import datetime, timedelta
    page = request.args.get('page', 1, type=int)
    per_page = 50
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status = request.args.get('status')
    location_id = request.args.get('location')
    search = request.args.get('search', '').strip()

    query = Attendance.query.join(User).join(Location)
    if date_from:
        query = query.filter(Attendance.attendance_date >= date_from)
    if date_to:
        query = query.filter(Attendance.attendance_date <= date_to)
    if status:
        query = query.filter(Attendance.status == status)
    if location_id:
        query = query.filter(Attendance.location_id == location_id)
    if search:
        query = query.filter(or_(
            User.full_name.ilike(f'%{search}%'),
            User.state_code.ilike(f'%{search}%'),
            User.email.ilike(f'%{search}%')
        ))
    attendance_records = query.order_by(Attendance.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    # Stats for dashboard
    total_corps_members = User.query.filter_by(is_admin=False).count()
    present_today = Attendance.query.filter(
        Attendance.attendance_date == datetime.utcnow().date(),
        Attendance.status == 'present'
    ).count()
    absent_today = total_corps_members - present_today
    attendance_rate = f"{(present_today / total_corps_members * 100):.1f}%" if total_corps_members else '0%'
    locations = Location.query.order_by(Location.name).all()

    # Real-time analytics data
    # 1. Attendance trend (last 7 days)
    today = datetime.utcnow().date()
    trend_labels = [(today - timedelta(days=i)).strftime('%a') for i in reversed(range(7))]
    trend_data = []
    for i in reversed(range(7)):
        day = today - timedelta(days=i)
        count = Attendance.query.filter(Attendance.attendance_date == day).count()
        trend_data.append(count)
    # 2. Present/Absent/Late breakdown (for current filters)
    filtered = query
    present_count = filtered.filter(Attendance.status == 'present').count()
    absent_count = filtered.filter(Attendance.status == 'absent').count()
    late_count = filtered.filter(Attendance.status == 'late').count()
    pie_data = [present_count, absent_count, late_count]
    # 3. Location-wise attendance (for current filters)
    location_labels = [loc.name for loc in locations]
    location_data = [filtered.filter(Attendance.location_id == loc.id).count() for loc in locations]

    return render_template(
        'admin/attendance.html',
        attendance_records=attendance_records,
        locations=locations,
        total_corps_members=total_corps_members,
        present_today=present_today,
        absent_today=absent_today,
        attendance_rate=attendance_rate,
        trend_labels=trend_labels,
        trend_data=trend_data,
        pie_data=pie_data,
        location_labels=location_labels,
        location_data=location_data
    )

@bp.route('/attendance/<int:attendance_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_attendance(attendance_id):
    """Delete an attendance record"""
    record = Attendance.query.get_or_404(attendance_id)
    try:
        db.session.delete(record)
        db.session.commit()
        flash('Attendance record deleted successfully.', 'success')
        return redirect(url_for('admin.attendance') + '#success')
    except Exception as e:
        flash(f'Error deleting attendance record: {str(e)}', 'danger')
        return redirect(url_for('admin.attendance') + '#error')

@bp.route('/attendance/<int:attendance_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_attendance(attendance_id):
    """Edit an attendance record"""
    record = Attendance.query.get_or_404(attendance_id)
    locations = Location.query.order_by(Location.name).all()
    users = User.query.order_by(User.full_name).all()
    if request.method == 'POST':
        try:
            record.user_id = request.form.get('user_id')
            record.location_id = request.form.get('location_id')
            record.attendance_date = request.form.get('date')
            record.check_in_time = request.form.get('check_in_time') or None
            record.check_out_time = request.form.get('check_out_time') or None
            record.status = request.form.get('status')
            record.recognition_method = request.form.get('attendance_method')
            db.session.commit()
            flash('Attendance record updated successfully.', 'success')
            return redirect(url_for('admin.attendance') + '#success')
        except Exception as e:
            flash(f'Error updating attendance record: {str(e)}', 'danger')
            return redirect(url_for('admin.attendance') + '#error')
    return render_template('admin/edit_attendance_modal.html', record=record, locations=locations, users=users)

@bp.route('/attendance/bulk_delete', methods=['POST'])
@login_required
@admin_required
def bulk_delete_attendance():
    ids = request.form.get('ids', '')
    if not ids:
        flash('No records selected.', 'danger')
        return redirect(url_for('admin.attendance') + '#error')
    id_list = [int(i) for i in ids.split(',') if i.isdigit()]
    try:
        Attendance.query.filter(Attendance.id.in_(id_list)).delete(synchronize_session=False)
        db.session.commit()
        flash(f'{len(id_list)} attendance records deleted.', 'success')
        return redirect(url_for('admin.attendance') + '#success')
    except Exception as e:
        flash(f'Error deleting records: {str(e)}', 'danger')
        return redirect(url_for('admin.attendance') + '#error')

@bp.route('/attendance/export', methods=['GET'])
@login_required
@admin_required
def export_attendance():
    format = request.args.get('format', 'csv')
    ids = request.args.get('ids', '')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    status = request.args.get('status')
    location_id = request.args.get('location')
    search = request.args.get('search', '').strip()
    query = Attendance.query.join(User).join(Location)
    if ids:
        id_list = [int(i) for i in ids.split(',') if i.isdigit()]
        query = query.filter(Attendance.id.in_(id_list))
    if date_from:
        query = query.filter(Attendance.attendance_date >= date_from)
    if date_to:
        query = query.filter(Attendance.attendance_date <= date_to)
    if status:
        query = query.filter(Attendance.status == status)
    if location_id:
        query = query.filter(Attendance.location_id == location_id)
    if search:
        query = query.filter(or_(
            User.full_name.ilike(f'%{search}%'),
            User.state_code.ilike(f'%{search}%'),
            User.email.ilike(f'%{search}%')
        ))
    records = query.order_by(Attendance.created_at.desc()).all()
    if format == 'csv':
        def generate():
            yield 'Date,Corps Member,State Code,Location,Check-in,Check-out,Status,Method\n'
            for r in records:
                yield f'{r.attendance_date},{r.user.full_name},{r.user.state_code},{r.location.name if r.location else "N/A"},{r.check_in_time or ""},{r.check_out_time or ""},{r.status},{r.recognition_method}\n'
        return Response(generate(), mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=attendance.csv"})
    elif format == 'excel':
        # Placeholder: implement Excel export
        return 'Excel export coming soon', 501
    elif format == 'pdf':
        # Placeholder: implement PDF export
        return 'PDF export coming soon', 501
    else:
        return 'Invalid format', 400

@bp.route('/reports')
@login_required
@admin_required
def reports():
    """Generate reports dashboard"""
    from datetime import date, timedelta
    from sqlalchemy import distinct
    
    # Get statistics for dashboard
    total_users = User.query.filter_by(is_admin=False).count()
    present_today = Attendance.query.filter(
        Attendance.attendance_date == date.today()
    ).count()
    attendance_rate = round((present_today / total_users * 100) if total_users > 0 else 0, 1)
    active_locations = Location.query.filter_by(is_active=True).count()
    
    # Get all locations and local governments for dropdowns
    locations = Location.query.order_by(Location.name).all()
    local_governments = db.session.query(distinct(User.local_government)).filter(
        User.local_government.isnot(None), User.local_government != ''
    ).order_by(User.local_government).all()
    local_governments = [lg[0] for lg in local_governments]
    
    # Get all unique states from state codes for dropdowns
    states_query = db.session.query(distinct(User.state_code)).filter(
        User.state_code.isnot(None), User.state_code != ''
    ).order_by(User.state_code).all()
    states = [state[0].split('/')[0] if '/' in state[0] else state[0] for state in states_query]
    states = sorted(list(set(states)))  # Remove duplicates and sort
    
    # Default date range (last 30 days)
    default_date_to = date.today()
    default_date_from = default_date_to - timedelta(days=30)
    
    return render_template('admin/reports.html',
                         total_users=total_users,
                         present_today=present_today,
                         attendance_rate=attendance_rate,
                         active_locations=active_locations,
                         locations=locations,
                         local_governments=local_governments,
                         states=states,
                         default_date_from=default_date_from.isoformat(),
                         default_date_to=default_date_to.isoformat())

# Report Generation Routes
@bp.route('/reports/attendance', methods=['POST'])
@login_required
@admin_required
def generate_attendance_report():
    """Generate attendance report"""
    try:
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        location_id = request.form.get('location_id')
        status = request.form.get('status')
        format = request.form.get('format', 'csv')
        
        # Build query
        query = Attendance.query.join(User).join(Location)
        if date_from:
            query = query.filter(Attendance.attendance_date >= date_from)
        if date_to:
            query = query.filter(Attendance.attendance_date <= date_to)
        if location_id:
            query = query.filter(Attendance.location_id == location_id)
        if status:
            query = query.filter(Attendance.status == status)
            
        records = query.order_by(Attendance.attendance_date.desc()).all()
        
        if format == 'csv':
            def generate():
                yield 'Date,Corps Member,State Code,Location,Check-in,Check-out,Status,Method\n'
                for r in records:
                    yield f'{r.attendance_date},{r.user.full_name},{r.user.state_code},{r.location.name if r.location else "N/A"},{r.check_in_time or ""},{r.check_out_time or ""},{r.status},{r.recognition_method}\n'
            return Response(generate(), mimetype='text/csv', 
                          headers={"Content-Disposition": "attachment;filename=attendance_report.csv"})
        else:
            flash('Excel and PDF formats coming soon!', 'info')
            return redirect(url_for('admin.reports'))
            
    except Exception as e:
        flash(f'Error generating report: {str(e)}', 'error')
        return redirect(url_for('admin.reports'))

@bp.route('/reports/users', methods=['POST'])
@login_required
@admin_required
def generate_user_report():
    """Generate user report"""
    try:
        report_type = request.form.get('report_type')
        state_filter = request.form.get('state_filter')
        format = request.form.get('format', 'csv')
        
        # Build query based on report type
        query = User.query.filter_by(is_admin=False)
        
        if report_type == 'active_users':
            query = query.filter_by(is_active=True)
        elif report_type == 'inactive_users':
            query = query.filter_by(is_active=False)
        elif report_type == 'users_with_face':
            query = query.filter(User.face_encoding.isnot(None))
        elif report_type == 'users_without_face':
            query = query.filter(User.face_encoding.is_(None))
            
        if state_filter:
            query = query.filter(User.state == state_filter)
            
        users = query.order_by(User.full_name).all()
        
        if format == 'csv':
            def generate():
                yield 'State Code,Full Name,Email,Phone,PPA,Local Government,Active,Has Face Data,Created\n'
                for u in users:
                    yield f'{u.state_code},{u.full_name},{u.email},{u.phone or ""},{u.ppa_name or ""},{u.local_government or ""},{"Yes" if u.is_active else "No"},{"Yes" if u.face_encoding else "No"},{u.created_at.strftime("%Y-%m-%d")}\n'
            return Response(generate(), mimetype='text/csv',
                          headers={"Content-Disposition": "attachment;filename=users_report.csv"})
        else:
            flash('Excel and PDF formats coming soon!', 'info')
            return redirect(url_for('admin.reports'))
            
    except Exception as e:
        flash(f'Error generating user report: {str(e)}', 'error')
        return redirect(url_for('admin.reports'))

@bp.route('/reports/locations', methods=['POST'])
@login_required
@admin_required
def generate_location_report():
    """Generate location report"""
    try:
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        location_id = request.form.get('location_id')
        format = request.form.get('format', 'csv')
        
        # Get locations with attendance data
        locations = Location.query.all()
        if location_id:
            locations = [Location.query.get(location_id)]
            
        if format == 'csv':
            def generate():
                yield 'Location,Address,State,Total Attendance,Date Range\n'
                for loc in locations:
                    query = Attendance.query.filter_by(location_id=loc.id)
                    if date_from:
                        query = query.filter(Attendance.attendance_date >= date_from)
                    if date_to:
                        query = query.filter(Attendance.attendance_date <= date_to)
                    total_attendance = query.count()
                    date_range = f'{date_from} to {date_to}' if date_from and date_to else 'All dates'
                    yield f'{loc.name},{loc.address or ""},{loc.state},{total_attendance},{date_range}\n'
            return Response(generate(), mimetype='text/csv',
                          headers={"Content-Disposition": "attachment;filename=locations_report.csv"})
        else:
            flash('Excel and PDF formats coming soon!', 'info')
            return redirect(url_for('admin.reports'))
            
    except Exception as e:
        flash(f'Error generating location report: {str(e)}', 'error')
        return redirect(url_for('admin.reports'))

@bp.route('/reports/summary', methods=['POST'])
@login_required
@admin_required
def generate_summary_report():
    """Generate summary report"""
    try:
        report_type = request.form.get('report_type')
        date_from = request.form.get('date_from')
        date_to = request.form.get('date_to')
        format = request.form.get('format', 'pdf')
        
        from datetime import date, timedelta
        
        # Determine date range based on report type
        if report_type == 'daily_summary':
            target_date = date.today()
            date_from = date_to = target_date.isoformat()
        elif report_type == 'weekly_summary':
            target_date = date.today()
            start_of_week = target_date - timedelta(days=target_date.weekday())
            date_from = start_of_week.isoformat()
            date_to = target_date.isoformat()
        elif report_type == 'monthly_summary':
            target_date = date.today()
            start_of_month = target_date.replace(day=1)
            date_from = start_of_month.isoformat()
            date_to = target_date.isoformat()
        
        # Generate summary statistics
        query = Attendance.query.join(User)
        if date_from:
            query = query.filter(Attendance.attendance_date >= date_from)
        if date_to:
            query = query.filter(Attendance.attendance_date <= date_to)
            
        attendances = query.all()
        total_present = len(attendances)
        on_time = len([a for a in attendances if a.status == 'present'])
        late = len([a for a in attendances if a.status == 'late'])
        very_late = len([a for a in attendances if a.status == 'very_late'])
        
        total_users = User.query.filter_by(is_admin=False, is_active=True).count()
        attendance_rate = (total_present / total_users * 100) if total_users > 0 else 0
        
        if format == 'csv':
            def generate():
                yield f'Summary Report - {report_type.replace("_", " ").title()}\n'
                yield f'Date Range,{date_from} to {date_to}\n'
                yield f'Total Present,{total_present}\n'
                yield f'On Time,{on_time}\n'
                yield f'Late,{late}\n'
                yield f'Very Late,{very_late}\n'
                yield f'Attendance Rate,{attendance_rate:.1f}%\n'
            return Response(generate(), mimetype='text/csv',
                          headers={"Content-Disposition": "attachment;filename=summary_report.csv"})
        else:
            flash('PDF and Excel formats coming soon!', 'info')
            return redirect(url_for('admin.reports'))
            
    except Exception as e:
        flash(f'Error generating summary report: {str(e)}', 'error')
        return redirect(url_for('admin.reports'))

# Quick Report Routes
@bp.route('/reports/daily')
@login_required
@admin_required
def generate_daily_report():
    """Generate today's attendance report"""
    try:
        today = date.today()
        attendances = Attendance.query.filter_by(attendance_date=today).join(User).join(Location).all()
        
        def generate():
            yield f'Daily Attendance Report - {today.strftime("%B %d, %Y")}\n'
            yield 'Corps Member,State Code,Location,Check-in Time,Status\n'
            for a in attendances:
                yield f'{a.user.full_name},{a.user.state_code},{a.location.name},{a.check_in_time.strftime("%H:%M") if a.check_in_time else "N/A"},{a.status}\n'
                
        return Response(generate(), mimetype='text/csv',
                      headers={"Content-Disposition": f"attachment;filename=daily_report_{today.isoformat()}.csv"})
        
    except Exception as e:
        flash(f'Error generating daily report: {str(e)}', 'error')
        return redirect(url_for('admin.reports'))

@bp.route('/reports/weekly')
@login_required
@admin_required
def generate_weekly_report():
    """Generate this week's attendance report"""
    try:
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        
        attendances = Attendance.query.filter(
            Attendance.attendance_date >= start_of_week,
            Attendance.attendance_date <= today
        ).join(User).join(Location).all()
        
        def generate():
            yield f'Weekly Attendance Report - {start_of_week.strftime("%B %d")} to {today.strftime("%B %d, %Y")}\n'
            yield 'Date,Corps Member,State Code,Location,Check-in Time,Status\n'
            for a in attendances:
                yield f'{a.attendance_date},{a.user.full_name},{a.user.state_code},{a.location.name},{a.check_in_time.strftime("%H:%M") if a.check_in_time else "N/A"},{a.status}\n'
                
        return Response(generate(), mimetype='text/csv',
                      headers={"Content-Disposition": f"attachment;filename=weekly_report_{start_of_week.isoformat()}_to_{today.isoformat()}.csv"})
        
    except Exception as e:
        flash(f'Error generating weekly report: {str(e)}', 'error')
        return redirect(url_for('admin.reports'))

@bp.route('/reports/monthly')
@login_required
@admin_required
def generate_monthly_report():
    """Generate this month's attendance report"""
    try:
        today = date.today()
        start_of_month = today.replace(day=1)
        
        attendances = Attendance.query.filter(
            Attendance.attendance_date >= start_of_month,
            Attendance.attendance_date <= today
        ).join(User).join(Location).all()
        
        def generate():
            yield f'Monthly Attendance Report - {start_of_month.strftime("%B %Y")}\n'
            yield 'Date,Corps Member,State Code,Location,Check-in Time,Status\n'
            for a in attendances:
                yield f'{a.attendance_date},{a.user.full_name},{a.user.state_code},{a.location.name},{a.check_in_time.strftime("%H:%M") if a.check_in_time else "N/A"},{a.status}\n'
                
        return Response(generate(), mimetype='text/csv',
                      headers={"Content-Disposition": f"attachment;filename=monthly_report_{start_of_month.strftime('%Y-%m')}.csv"})
        
    except Exception as e:
        flash(f'Error generating monthly report: {str(e)}', 'error')
        return redirect(url_for('admin.reports'))

@bp.route('/reports/email_summary')
@login_required
@admin_required
def send_daily_summary_email():
    """Send daily summary via email"""
    try:
        from app.services.notification_service import NotificationService
        notification_service = NotificationService()
        
        success = notification_service.send_daily_attendance_report()
        if success:
            flash('Daily summary email sent successfully!', 'success')
        else:
            flash('Failed to send daily summary email. Please check email configuration.', 'error')
            
    except Exception as e:
        flash(f'Error sending daily summary email: {str(e)}', 'error')
        
    return redirect(url_for('admin.reports'))

@bp.route('/send_announcement', methods=['POST'])
@login_required
@admin_required
def send_announcement():
    """Send announcement to all corps members"""
    try:
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        priority = request.form.get('priority', 'low')
        is_active = bool(request.form.get('is_active'))
        if not title or not message:
            flash('Title and message are required.', 'error')
            return redirect(url_for('admin.announcements'))
        from app.models import Announcement
        announcement = Announcement(
            title=title,
            message=message,
            priority=priority,
            is_active=is_active,
            is_urgent=(priority == 'high'),
            created_by=current_user.id
        )
        db.session.add(announcement)
        db.session.commit()
        flash(f'Announcement "{title}" has been sent successfully!', 'success')
        return redirect(url_for('admin.announcements'))
    except Exception as e:
        flash(f'Error sending announcement: {str(e)}', 'error')
        return redirect(url_for('admin.announcements'))

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

@bp.route('/announcement/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_announcement(id):
    from app.models import Announcement
    announcement = Announcement.query.get_or_404(id)
    announcement.is_active = not announcement.is_active
    db.session.commit()
    flash(f'Announcement "{announcement.title}" has been {"activated" if announcement.is_active else "deactivated"}.', 'success')
    return redirect(url_for('admin.announcements'))

@bp.route('/announcement/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_announcement(id):
    from app.models import Announcement
    announcement = Announcement.query.get_or_404(id)
    db.session.delete(announcement)
    db.session.commit()
    flash(f'Announcement "{announcement.title}" deleted.', 'success')
    return redirect(url_for('admin.announcements'))

@bp.route('/announcement/<int:id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_announcement(id):
    from app.models import Announcement
    announcement = Announcement.query.get_or_404(id)
    announcement.title = request.form.get('title')
    announcement.message = request.form.get('message')
    announcement.priority = request.form.get('priority')
    announcement.is_active = bool(request.form.get('is_active'))
    announcement.is_urgent = (announcement.priority == 'high')
    db.session.commit()
    flash(f'Announcement "{announcement.title}" updated.', 'success')
    return redirect(url_for('admin.announcements'))

@bp.route('/attendance/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_attendance():
    users = User.query.order_by(User.full_name).all()
    locations = Location.query.order_by(Location.name).all()
    from datetime import date
    today = date.today().isoformat()
    if request.method == 'POST':
        try:
            user_id = request.form.get('user_id')
            location_id = request.form.get('location_id')
            attendance_date = request.form.get('date')
            check_in_time = request.form.get('check_in_time')
            check_out_time = request.form.get('check_out_time')
            status = request.form.get('status')
            recognition_method = request.form.get('attendance_method')
            if not (user_id and location_id and attendance_date and status):
                flash('All required fields must be filled.', 'danger')
                return redirect(url_for('admin.attendance') + '#error')
            from app.models import Attendance
            from datetime import datetime
            record = Attendance(
                user_id=user_id,
                location_id=location_id,
                attendance_date=attendance_date,
                check_in_time=datetime.combine(datetime.strptime(attendance_date, '%Y-%m-%d'), datetime.strptime(check_in_time, '%H:%M').time()) if check_in_time else None,
                check_out_time=datetime.combine(datetime.strptime(attendance_date, '%Y-%m-%d'), datetime.strptime(check_out_time, '%H:%M').time()) if check_out_time else None,
                status=status,
                recognition_method=recognition_method or 'manual'
            )
            db.session.add(record)
            db.session.commit()
            flash('Attendance record added successfully.', 'success')
            return redirect(url_for('admin.attendance') + '#success')
        except Exception as e:
            flash(f'Error adding attendance record: {str(e)}', 'danger')
            return redirect(url_for('admin.attendance') + '#error')
    return render_template('admin/add_attendance_modal.html', users=users, locations=locations, today=today)
