from datetime import datetime, date, timedelta
from app import db
from app.models import User, Attendance, Location, CDSchedule
from app.services.face_recognition_service import FaceRecognitionService
import logging

logger = logging.getLogger(__name__)

class AttendanceService:
    """Service for handling attendance operations"""
    
    def __init__(self):
        self.face_service = FaceRecognitionService()
    
    def mark_attendance_by_face_and_pin(self, state_code: str, pin: str, location_id: int) -> dict:
        """Mark attendance using face recognition and a secure PIN"""
        try:
            # Verify PIN
            user = User.query.filter_by(state_code=state_code, is_active=True).first()
            if not user:
                return {
                    'success': False,
                    'message': 'Invalid state code or inactive account.',
                    'user_id': None
                }

            if not user.check_pin(pin):
                return {
                    'success': False,
                    'message': 'Invalid PIN.',
                    'user_id': user.id
                }

            # Recognize face from camera
            recognized_user_id, confidence = self.face_service.recognize_face_from_camera()

            if recognized_user_id != user.id:
                return {
                    'success': False,
                    'message': 'Face not recognized or mismatch. Please try again or contact admin.',
                    'user_id': user.id
                }

            # Check if location is scheduled for today
            if not self.is_location_scheduled_today(location_id):
                return {
                    'success': False,
                    'message': 'This location is not scheduled for today.',
                    'user_id': user.id
                }

            # Check if already marked attendance today
            today = date.today()
            existing_attendance = Attendance.query.filter_by(
                user_id=user.id,
                location_id=location_id,
                attendance_date=today
            ).first()

            if existing_attendance:
                return {
                    'success': False,
                    'message': f'Attendance already marked today at {existing_attendance.check_in_time.strftime("%H:%M")}',
                    'user_id': user.id,
                    'user_name': user.full_name
                }

            # Create attendance record
            attendance = Attendance(
                user_id=user.id,
                location_id=location_id,
                recognition_method='face_pin',
                confidence_score=confidence,
                status=self._determine_attendance_status()
            )

            db.session.add(attendance)
            db.session.commit()

            logger.info(f"Attendance marked for user {user.id} at location {location_id}")

            return {
                'success': True,
                'message': f'Attendance marked successfully for {user.full_name}',
                'user_id': user.id,
                'user_name': user.full_name,
                'confidence': confidence,
                'check_in_time': attendance.check_in_time.strftime("%H:%M")
            }

        except Exception as e:
            logger.error(f"Error marking attendance by face and PIN: {str(e)}")
            return {
                'success': False,
                'message': 'System error occurred. Please try again.',
                'user_id': None
            }

    def is_location_scheduled_today(self, location_id: int) -> bool:
        """Check if a location is scheduled for today"""
        schedule = CDSchedule.get_active_schedule_for_location(location_id)
        return schedule is not None and schedule.is_active_now()

    def _determine_attendance_status(self) -> str:
        """Determine attendance status based on check-in time"""
        current_time = datetime.now().time()

        # Assuming CD activities start at 8:00 AM
        if current_time <= datetime.strptime("08:00", "%H:%M").time():
            return 'present'
        elif current_time <= datetime.strptime("08:30", "%H:%M").time():
            return 'late'
        else:
            return 'very_late'

    def get_user_attendance_history(self, user_id: int, days: int = 30) -> list:
        """Get attendance history for a user"""
        try:
            start_date = date.today() - timedelta(days=days)

            attendances = Attendance.query.filter(
                Attendance.user_id == user_id,
                Attendance.attendance_date >= start_date
            ).order_by(Attendance.attendance_date.desc()).all()

            return [attendance.to_dict() for attendance in attendances]

        except Exception as e:
            logger.error(f"Error getting attendance history: {str(e)}")
            return []

    def mark_attendance(self, user_id: int, schedule_id: int, method: str = 'manual') -> dict:
        """Mark attendance for a user at a scheduled location"""
        try:
            # Get user and schedule
            user = User.query.get(user_id)
            schedule = CDSchedule.query.get(schedule_id)
            
            if not user:
                return {'success': False, 'message': 'User not found'}
            
            if not schedule:
                return {'success': False, 'message': 'Schedule not found'}
            
            if not schedule.can_mark_attendance():
                return {'success': False, 'message': 'Cannot mark attendance for this schedule'}
            
            # Check if already marked for today
            existing_attendance = Attendance.query.filter_by(
                user_id=user_id,
                location_id=schedule.location_id,
                attendance_date=date.today()
            ).first()
            
            if existing_attendance:
                return {
                    'success': False, 
                    'message': f'Attendance already marked today at {existing_attendance.check_in_time.strftime("%H:%M")}'
                }
            
            # Create attendance record
            attendance = Attendance(
                user_id=user_id,
                location_id=schedule.location_id,
                recognition_method=method,
                status=self._determine_attendance_status()
            )
            
            db.session.add(attendance)
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Attendance marked successfully for {user.full_name}',
                'attendance_id': attendance.id
            }
            
        except Exception as e:
            logger.error(f"Error marking attendance: {str(e)}")
            return {'success': False, 'message': 'System error occurred'}
    
    def get_location_attendance_summary(self, location_id: int, target_date: date = None) -> dict:
        """Get attendance summary for a location on a specific date"""
        if target_date is None:
            target_date = date.today()

        try:
            attendances = Attendance.query.filter_by(
                location_id=location_id,
                attendance_date=target_date
            ).all()

            total_present = len(attendances)
            on_time = len([a for a in attendances if a.status == 'present'])
            late = len([a for a in attendances if a.status in ['late', 'very_late']])

            return {
                'date': target_date.isoformat(),
                'total_present': total_present,
                'on_time': on_time,
                'late': late,
                'attendance_rate': (total_present / max(User.query.filter_by(is_active=True).count(), 1)) * 100
            }

        except Exception as e:
            logger.error(f"Error getting location attendance summary: {str(e)}")
            return {}
