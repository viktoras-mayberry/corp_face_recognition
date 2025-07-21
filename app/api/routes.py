from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from app.api import bp
from app.models import User, Attendance, Location, CDSchedule
from app.services.attendance_service import AttendanceService
from app.services.face_recognition_service import FaceRecognitionService
from app import db
from datetime import date, datetime
import os

@bp.route('/attendance/mark', methods=['POST'])
@login_required
def mark_attendance():
    """Mark attendance via API"""
    try:
        data = request.get_json()
        schedule_id = data.get('schedule_id')
        method = data.get('method', 'manual')  # manual, face_recognition, qr_code
        
        if not schedule_id:
            return jsonify({'error': 'Schedule ID is required'}), 400
        
        # Get schedule
        schedule = CDSchedule.query.get(schedule_id)
        if not schedule:
            return jsonify({'error': 'Schedule not found'}), 404
        
        if not schedule.is_active:
            return jsonify({'error': 'Schedule is not active'}), 400
        
        # Check if already marked for today
        existing_attendance = Attendance.query.filter_by(
            user_id=current_user.id,
            location_id=schedule.location_id,
            attendance_date=date.today()
        ).first()
        
        if existing_attendance:
            return jsonify({'error': 'Attendance already marked for this schedule today'}), 400
        
        # Mark attendance
        attendance_service = AttendanceService()
        result = attendance_service.mark_attendance(
            user_id=current_user.id,
            schedule_id=schedule_id,
            method=method
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Attendance marked successfully',
                'attendance_id': result['attendance_id']
            })
        else:
            return jsonify({'error': result['message']}), 400
            
    except Exception as e:
        current_app.logger.error(f"Error marking attendance: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/attendance/history')
@login_required
def attendance_history():
    """Get user's attendance history"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        if per_page > 100:  # Limit to prevent abuse
            per_page = 100
        
        attendance_records = Attendance.query.filter_by(
            user_id=current_user.id
        ).order_by(Attendance.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'attendance_records': [{
                'id': record.id,
                'location_id': record.location_id,
                'location_name': record.location.name if record.location else 'N/A',
                'attendance_date': record.attendance_date.isoformat(),
                'created_at': record.created_at.isoformat(),
                'recognition_method': record.recognition_method,
                'status': record.status
            } for record in attendance_records.items],
            'total': attendance_records.total,
            'pages': attendance_records.pages,
            'current_page': page
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching attendance history: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/schedules/today')
@login_required
def todays_schedules():
    """Get today's schedules"""
    try:
        schedules = CDSchedule.query.filter_by(
            schedule_date=date.today(),
            is_active=True
        ).all()
        
        return jsonify({
            'schedules': [{
                'id': schedule.id,
                'location_name': schedule.location.name if schedule.location else 'N/A',
                'location_address': schedule.location.address if schedule.location else 'N/A',
                'start_time': schedule.start_time.strftime('%H:%M'),
                'end_time': schedule.end_time.strftime('%H:%M'),
                'activity_type': schedule.activity_type,
                'description': schedule.description,
                'expected_attendees': schedule.expected_attendees
            } for schedule in schedules]
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching today's schedules: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/face_recognition/upload', methods=['POST'])
@login_required
def upload_face_image():
    """Upload face image for recognition"""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file:
            # Save and process the image
            face_service = FaceRecognitionService()
            result = face_service.save_user_face_image(current_user.id, file)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'message': 'Face image uploaded and processed successfully'
                })
            else:
                return jsonify({'error': result['message']}), 400
                
    except Exception as e:
        current_app.logger.error(f"Error uploading face image: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/user/profile')
@login_required
def user_profile():
    """Get current user's profile"""
    try:
        return jsonify({
            'user': {
                'id': current_user.id,
                'state_code': current_user.state_code,
                'full_name': current_user.full_name,
                'email': current_user.email,
                'is_admin': current_user.is_admin,
                'is_active': current_user.is_active,
                'email_verified': current_user.email_verified,
                'face_registered': current_user.face_encoding is not None,
                'created_at': current_user.created_at.isoformat(),
                'last_login': current_user.last_login.isoformat() if current_user.last_login else None
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Error fetching user profile: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500
