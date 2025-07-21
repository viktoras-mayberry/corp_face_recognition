from datetime import datetime, date
from app import db

class CDSchedule(db.Model):
    """CD Schedule for managing which locations are active on specific dates"""
    __tablename__ = 'cd_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    
    # Schedule Details
    schedule_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False, default=datetime.strptime("08:00", "%H:%M").time())
    end_time = db.Column(db.Time, nullable=False, default=datetime.strptime("16:00", "%H:%M").time())
    
    # Activity Details
    activity_type = db.Column(db.String(100), default="Community Development")
    description = db.Column(db.Text, nullable=True)
    expected_attendees = db.Column(db.Integer, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_cancelled = db.Column(db.Boolean, default=False)
    cancellation_reason = db.Column(db.Text, nullable=True)
    
    # Admin who set the schedule
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_current(self):
        """Check if this schedule is for today"""
        return self.schedule_date == date.today()
    
    def is_active_now(self):
        """Check if the schedule is currently active (within start and end time)"""
        if not self.is_current() or not self.is_active or self.is_cancelled:
            return False
        
        current_time = datetime.now().time()
        return self.start_time <= current_time <= self.end_time
    
    def can_mark_attendance(self):
        """Check if attendance can be marked for this schedule"""
        return self.is_current() and self.is_active and not self.is_cancelled
    
    @staticmethod
    def get_today_active_locations():
        """Get all active locations for today"""
        from .location import Location
        
        today_schedules = CDSchedule.query.filter_by(
            schedule_date=date.today(),
            is_active=True,
            is_cancelled=False
        ).all()
        
        location_ids = [schedule.location_id for schedule in today_schedules]
        return Location.query.filter(Location.id.in_(location_ids)).all()
    
    @staticmethod
    def get_active_schedule_for_location(location_id):
        """Get active schedule for a specific location today"""
        return CDSchedule.query.filter_by(
            location_id=location_id,
            schedule_date=date.today(),
            is_active=True,
            is_cancelled=False
        ).first()
    
    def cancel_schedule(self, reason=""):
        """Cancel the schedule"""
        self.is_cancelled = True
        self.cancellation_reason = reason
        db.session.commit()
    
    def activate_schedule(self):
        """Activate the schedule"""
        self.is_active = True
        self.is_cancelled = False
        self.cancellation_reason = None
        db.session.commit()
    
    def to_dict(self):
        return {
            'id': self.id,
            'location_id': self.location_id,
            'schedule_date': self.schedule_date.isoformat(),
            'start_time': self.start_time.strftime("%H:%M"),
            'end_time': self.end_time.strftime("%H:%M"),
            'activity_type': self.activity_type,
            'description': self.description,
            'expected_attendees': self.expected_attendees,
            'is_active': self.is_active,
            'is_cancelled': self.is_cancelled,
            'cancellation_reason': self.cancellation_reason,
            'created_by': self.created_by,
            'is_current': self.is_current(),
            'is_active_now': self.is_active_now(),
            'can_mark_attendance': self.can_mark_attendance(),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
    
    def __repr__(self):
        return f'<CDSchedule Location {self.location_id} on {self.schedule_date}>'
