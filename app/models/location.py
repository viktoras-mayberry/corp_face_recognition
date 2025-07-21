from datetime import datetime
from app import db

class Location(db.Model):
    """CD locations where attendance can be marked"""
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=True)
    local_government = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    
    # Location coordinates (for future GPS features)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    # Camera/Device settings
    camera_id = db.Column(db.String(50), nullable=True)  # Camera identifier or index
    camera_name = db.Column(db.String(100), nullable=True)  # Human-readable camera name
    
    # Status and metadata
    is_active = db.Column(db.Boolean, default=True)
    max_capacity = db.Column(db.Integer, nullable=True)  # Maximum expected attendees
    description = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    attendance_records = db.relationship('Attendance', backref='location', lazy='dynamic', cascade='all, delete-orphan')
    cd_schedules = db.relationship('CDSchedule', backref='location', lazy='dynamic')
    
    def get_today_attendance_count(self):
        """Get total attendance count for today"""
        from datetime import date
        from .attendance import Attendance
        
        return Attendance.query.filter_by(
            location_id=self.id,
            attendance_date=date.today()
        ).count()
    
    def get_attendance_summary(self, target_date=None):
        """Get attendance summary for a specific date"""
        from datetime import date
        from .attendance import Attendance
        
        if target_date is None:
            target_date = date.today()
        
        attendances = Attendance.query.filter_by(
            location_id=self.id,
            attendance_date=target_date
        ).all()
        
        total_present = len(attendances)
        on_time = len([a for a in attendances if a.status == 'present'])
        late = len([a for a in attendances if a.status == 'late'])
        very_late = len([a for a in attendances if a.status == 'very_late'])
        face_recognition = len([a for a in attendances if a.recognition_method == 'face'])
        pin_method = len([a for a in attendances if a.recognition_method == 'pin'])
        
        return {
            'date': target_date.isoformat(),
            'total_present': total_present,
            'on_time': on_time,
            'late': late,
            'very_late': very_late,
            'face_recognition': face_recognition,
            'pin_method': pin_method,
            'capacity_utilization': (total_present / self.max_capacity) * 100 if self.max_capacity else None
        }
    
    def is_scheduled_today(self):
        """Check if this location is scheduled for today"""
        from datetime import date
        from .cd_schedule import CDSchedule
        
        return CDSchedule.query.filter_by(
            location_id=self.id,
            schedule_date=date.today(),
            is_active=True
        ).first() is not None
    
    def get_current_schedule(self):
        """Get today's schedule for this location"""
        from datetime import date
        from .cd_schedule import CDSchedule
        
        return CDSchedule.query.filter_by(
            location_id=self.id,
            schedule_date=date.today(),
            is_active=True
        ).first()
    
    def to_dict(self, include_stats=False):
        """Convert location to dictionary"""
        data = {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'local_government': self.local_government,
            'state': self.state,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'camera_id': self.camera_id,
            'camera_name': self.camera_name,
            'is_active': self.is_active,
            'max_capacity': self.max_capacity,
            'description': self.description,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_scheduled_today': self.is_scheduled_today()
        }
        
        if include_stats:
            data.update({
                'today_attendance_count': self.get_today_attendance_count(),
                'attendance_summary': self.get_attendance_summary(),
                'current_schedule': self.get_current_schedule().to_dict() if self.get_current_schedule() else None
            })
        
        return data
    
    def __repr__(self):
        return f'<Location {self.name} - {self.local_government}, {self.state}>'
