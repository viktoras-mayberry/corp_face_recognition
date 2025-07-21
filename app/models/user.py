from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app import db
import json
import secrets

class User(UserMixin, db.Model):
    """User model for corps members and admins"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Personal Information
    state_code = db.Column(db.String(15), unique=True, nullable=False, index=True)  # e.g., "NY/23A/1234"
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    
    # Authentication
    password_hash = db.Column(db.String(200), nullable=False)
    pin_hash = db.Column(db.String(200), nullable=False)  # 4-digit PIN
    
    # Face Recognition Data
    face_encoding = db.Column(db.Text, nullable=True)  # JSON encoded face data
    face_image_path = db.Column(db.String(255), nullable=True)
    
    # Account Status
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    
    # Corps Information
    ppa_name = db.Column(db.String(200), nullable=True)  # Primary Place of Assignment
    cd_group = db.Column(db.String(50), nullable=True)   # CD Group
    local_government = db.Column(db.String(100), nullable=True)
    batch = db.Column(db.String(10), nullable=True)      # e.g., "Batch C"
    
    # Security Features
    failed_login_attempts = db.Column(db.Integer, default=0)
    account_locked_until = db.Column(db.DateTime, nullable=True)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password"""
        return check_password_hash(self.password_hash, password)
    
    def set_pin(self, pin):
        """Set PIN hash"""
        if len(str(pin)) != 4 or not str(pin).isdigit():
            raise ValueError("PIN must be exactly 4 digits")
        self.pin_hash = generate_password_hash(str(pin))
    
    def check_pin(self, pin):
        """Check PIN"""
        return check_password_hash(self.pin_hash, str(pin))
    
    def set_face_encoding(self, encoding_array):
        """Store face encoding as JSON"""
        if encoding_array is not None:
            self.face_encoding = json.dumps(encoding_array.tolist())
    
    def get_face_encoding(self):
        """Retrieve face encoding as numpy array"""
        if self.face_encoding:
            import numpy as np
            return np.array(json.loads(self.face_encoding))
        return None
    
    def is_account_locked(self):
        """Check if account is locked due to failed login attempts"""
        if self.account_locked_until and datetime.utcnow() < self.account_locked_until:
            return True
        return False
    
    def lock_account(self, minutes=30):
        """Lock account for specified minutes"""
        from datetime import timedelta
        self.account_locked_until = datetime.utcnow() + timedelta(minutes=minutes)
        db.session.commit()
    
    def unlock_account(self):
        """Unlock account and reset failed attempts"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        db.session.commit()
    
    def increment_failed_login(self):
        """Increment failed login attempts and lock if necessary"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:  # Lock after 5 failed attempts
            self.lock_account(30)  # Lock for 30 minutes
        db.session.commit()
    
    def generate_reset_token(self):
        """Generate password reset token"""
        from datetime import timedelta
        self.reset_token = secrets.token_urlsafe(32)
        self.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        return self.reset_token
    
    def verify_reset_token(self, token):
        """Verify password reset token"""
        if (self.reset_token == token and 
            self.reset_token_expires and 
            datetime.utcnow() < self.reset_token_expires):
            return True
        return False
    
    def clear_reset_token(self):
        """Clear reset token after use"""
        self.reset_token = None
        self.reset_token_expires = None
        db.session.commit()
    
    def has_face_data(self):
        """Check if user has face recognition data"""
        return self.face_encoding is not None
    
    def get_attendance_summary(self, days=30):
        """Get attendance summary for the user"""
        from datetime import date, timedelta
        from .attendance import Attendance
        
        start_date = date.today() - timedelta(days=days)
        attendances = Attendance.query.filter(
            Attendance.user_id == self.id,
            Attendance.attendance_date >= start_date
        ).all()
        
        total_days = days
        present_days = len(attendances)
        on_time = len([a for a in attendances if a.status == 'present'])
        late = len([a for a in attendances if a.status in ['late', 'very_late']])
        
        return {
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': total_days - present_days,
            'on_time': on_time,
            'late': late,
            'attendance_rate': (present_days / total_days) * 100 if total_days > 0 else 0
        }
    
    def to_dict(self, include_sensitive=False):
        """Convert user to dictionary"""
        data = {
            'id': self.id,
            'state_code': self.state_code,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'email_verified': self.email_verified,
            'ppa_name': self.ppa_name,
            'cd_group': self.cd_group,
            'local_government': self.local_government,
            'batch': self.batch,
            'has_face_data': self.has_face_data(),
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'updated_at': self.updated_at.isoformat()
        }
        
        if include_sensitive:
            data.update({
                'failed_login_attempts': self.failed_login_attempts,
                'is_locked': self.is_account_locked(),
                'face_image_path': self.face_image_path
            })
        
        return data
    
    def __repr__(self):
        return f'<User {self.state_code}: {self.full_name}>'
