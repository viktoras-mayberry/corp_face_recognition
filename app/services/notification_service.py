import logging
from flask import current_app
from flask_mail import Message, Mail
from twilio.rest import Client
from app.models import User, Attendance
from datetime import date, datetime
import os

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for handling email and SMS notifications"""
    
    def __init__(self):
        self.mail = None
        self.twilio_client = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize email and SMS services"""
        try:
            # Initialize Flask-Mail
            if current_app:
                self.mail = Mail(current_app)
            
            # Initialize Twilio
            account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
            auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
            
            if account_sid and auth_token:
                self.twilio_client = Client(account_sid, auth_token)
                
        except Exception as e:
            logger.error(f"Error initializing notification services: {str(e)}")
    
    def send_attendance_confirmation_email(self, user: User, attendance: Attendance) -> bool:
        """Send attendance confirmation email to user"""
        try:
            if not self.mail or not user.email:
                return False
            
            msg = Message(
                subject='Attendance Confirmation - NYSC CD',
                sender=current_app.config['ADMIN_EMAIL'],
                recipients=[user.email]
            )
            
            msg.body = f"""
            Dear {user.full_name},
            
            Your attendance has been successfully recorded for today's Community Development activity.
            
            Details:
            - Date: {attendance.attendance_date.strftime('%B %d, %Y')}
            - Check-in Time: {attendance.check_in_time.strftime('%H:%M')}
            - Status: {attendance.status.title()}
            - Location: {attendance.location.name}
            
            Thank you for your participation!
            
            Best regards,
            NYSC Corps Attendance System
            """
            
            msg.html = f"""
            <html>
            <body>
                <h2>Attendance Confirmation</h2>
                <p>Dear {user.full_name},</p>
                
                <p>Your attendance has been successfully recorded for today's Community Development activity.</p>
                
                <h3>Details:</h3>
                <ul>
                    <li><strong>Date:</strong> {attendance.attendance_date.strftime('%B %d, %Y')}</li>
                    <li><strong>Check-in Time:</strong> {attendance.check_in_time.strftime('%H:%M')}</li>
                    <li><strong>Status:</strong> {attendance.status.title()}</li>
                    <li><strong>Location:</strong> {attendance.location.name}</li>
                </ul>
                
                <p>Thank you for your participation!</p>
                
                <p>Best regards,<br>
                NYSC Corps Attendance System</p>
            </body>
            </html>
            """
            
            self.mail.send(msg)
            logger.info(f"Attendance confirmation email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending attendance confirmation email: {str(e)}")
            return False
    
    def send_attendance_confirmation_sms(self, user: User, attendance: Attendance) -> bool:
        """Send attendance confirmation SMS to user"""
        try:
            if not self.twilio_client or not user.phone:
                return False
            
            message_body = f"""
            NYSC CD Attendance Confirmed
            
            Dear {user.full_name.split()[0]},
            Your attendance for {attendance.attendance_date.strftime('%d/%m/%Y')} at {attendance.check_in_time.strftime('%H:%M')} has been recorded.
            Status: {attendance.status.title()}
            Location: {attendance.location.name}
            
            Thank you!
            """
            
            message = self.twilio_client.messages.create(
                body=message_body,
                from_=os.environ.get('TWILIO_PHONE_NUMBER'),
                to=user.phone
            )
            
            logger.info(f"Attendance confirmation SMS sent to {user.phone}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending attendance confirmation SMS: {str(e)}")
            return False
    
    def send_admin_notification_email(self, subject: str, body: str, html_body: str = None) -> bool:
        """Send notification email to admin"""
        try:
            if not self.mail:
                return False
            
            admin_email = current_app.config['ADMIN_EMAIL']
            
            msg = Message(
                subject=f"[NYSC Attendance] {subject}",
                sender=admin_email,
                recipients=[admin_email]
            )
            
            msg.body = body
            if html_body:
                msg.html = html_body
            
            self.mail.send(msg)
            logger.info(f"Admin notification email sent: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending admin notification email: {str(e)}")
            return False
    
    def send_admin_notification_sms(self, message: str) -> bool:
        """Send notification SMS to admin"""
        try:
            if not self.twilio_client:
                return False
            
            # You would need to configure admin phone number in environment
            admin_phone = os.environ.get('ADMIN_PHONE_NUMBER')
            if not admin_phone:
                return False
            
            self.twilio_client.messages.create(
                body=f"[NYSC Attendance] {message}",
                from_=os.environ.get('TWILIO_PHONE_NUMBER'),
                to=admin_phone
            )
            
            logger.info("Admin notification SMS sent")
            return True
            
        except Exception as e:
            logger.error(f"Error sending admin notification SMS: {str(e)}")
            return False
    
    def send_daily_attendance_report(self, target_date: date = None) -> bool:
        """Send daily attendance report to admin"""
        try:
            if target_date is None:
                target_date = date.today()
            
            # Get attendance statistics
            attendances = Attendance.query.filter_by(attendance_date=target_date).all()
            
            total_present = len(attendances)
            on_time = len([a for a in attendances if a.status == 'present'])
            late = len([a for a in attendances if a.status == 'late'])
            very_late = len([a for a in attendances if a.status == 'very_late'])
            
            # Email report
            subject = f"Daily Attendance Report - {target_date.strftime('%B %d, %Y')}"
            
            body = f"""
            Daily Attendance Report
            Date: {target_date.strftime('%B %d, %Y')}
            
            Summary:
            - Total Present: {total_present}
            - On Time: {on_time}
            - Late: {late}
            - Very Late: {very_late}
            
            Attendance Rate: {(total_present / max(User.query.filter_by(is_active=True).count(), 1)) * 100:.1f}%
            
            System Administrator
            NYSC Corps Attendance System
            """
            
            html_body = f"""
            <html>
            <body>
                <h2>Daily Attendance Report</h2>
                <p><strong>Date:</strong> {target_date.strftime('%B %d, %Y')}</p>
                
                <h3>Summary:</h3>
                <table border="1" style="border-collapse: collapse; width: 100%;">
                    <tr><td><strong>Total Present</strong></td><td>{total_present}</td></tr>
                    <tr><td><strong>On Time</strong></td><td>{on_time}</td></tr>
                    <tr><td><strong>Late</strong></td><td>{late}</td></tr>
                    <tr><td><strong>Very Late</strong></td><td>{very_late}</td></tr>
                    <tr><td><strong>Attendance Rate</strong></td><td>{(total_present / max(User.query.filter_by(is_active=True).count(), 1)) * 100:.1f}%</td></tr>
                </table>
                
                <p>System Administrator<br>
                NYSC Corps Attendance System</p>
            </body>
            </html>
            """
            
            return self.send_admin_notification_email(subject, body, html_body)
            
        except Exception as e:
            logger.error(f"Error sending daily attendance report: {str(e)}")
            return False
    
    def send_absence_alert(self, absent_users: list) -> bool:
        """Send alert for users who are absent"""
        try:
            if not absent_users:
                return True
            
            subject = f"Absence Alert - {len(absent_users)} Corps Members Absent"
            
            absent_list = "\n".join([f"- {user.full_name} ({user.state_code})" for user in absent_users])
            
            body = f"""
            Absence Alert
            Date: {date.today().strftime('%B %d, %Y')}
            
            The following Corps members are absent from today's CD activity:
            
            {absent_list}
            
            Total Absent: {len(absent_users)}
            
            Please follow up as necessary.
            
            System Administrator
            NYSC Corps Attendance System
            """
            
            return self.send_admin_notification_email(subject, body)
            
        except Exception as e:
            logger.error(f"Error sending absence alert: {str(e)}")
            return False
