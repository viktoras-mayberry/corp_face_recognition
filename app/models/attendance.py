from datetime import datetime
from app import db

class Attendance(db.Model):
    """Attendance records for corps members"""
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    
    # Attendance Details
    check_in_time = db.Column(db.DateTime, default=datetime.utcnow)
    check_out_time = db.Column(db.DateTime, nullable=True)
    attendance_date = db.Column(db.Date, default=datetime.utcnow().date())
    
    # Recognition Details
    recognition_method = db.Column(db.String(20), nullable=False)  # 'face', 'pin'
    confidence_score = db.Column(db.Float, nullable=True)  # Face recognition confidence
    
    # Status
    status = db.Column(db.String(20), nullable=False)  # present, late, very_late
    notes = db.Column(db.Text, nullable=True)  # Additional notes
    
    # Verification
    verified_by_admin = db.Column(db.Boolean, default=False)
    admin_notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def mark_checkout(self):
        """Mark check-out time"""
        self.check_out_time = datetime.utcnow()
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'location_id': self.location_id,
            'check_in_time': self.check_in_time.isoformat(),
            'check_out_time': self.check_out_time.isoformat() if self.check_out_time else None,
            'attendance_date': self.attendance_date.isoformat(),
            'recognition_method': self.recognition_method,
            'confidence_score': self.confidence_score,
            'status': self.status,
            'notes': self.notes,
            'verified_by_admin': self.verified_by_admin,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<Attendance User {self.user_id} at {self.location_id} on {self.attendance_date}>'
