from datetime import datetime
from app import db

class Announcement(db.Model):
    """Announcements/Updates from admin to corps members"""
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Type of announcement (info, warning, success, danger)
    announcement_type = db.Column(db.String(20), default='info')
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_urgent = db.Column(db.Boolean, default=False)
    
    # Admin who created the announcement
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)  # Optional expiry date
    
    # Relationship
    creator = db.relationship('User', backref='announcements')
    
    def is_expired(self):
        """Check if announcement has expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def is_visible(self):
        """Check if announcement should be displayed"""
        return self.is_active and not self.is_expired()
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'announcement_type': self.announcement_type,
            'is_active': self.is_active,
            'is_urgent': self.is_urgent,
            'created_by': self.created_by,
            'creator_name': self.creator.full_name if self.creator else 'Admin',
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_expired': self.is_expired(),
            'is_visible': self.is_visible()
        }
    
    @staticmethod
    def get_active_announcements():
        """Get all active, non-expired announcements"""
        return Announcement.query.filter_by(is_active=True).filter(
            (Announcement.expires_at.is_(None)) | 
            (Announcement.expires_at > datetime.utcnow())
        ).order_by(Announcement.is_urgent.desc(), Announcement.created_at.desc()).all()
    
    def __repr__(self):
        return f'<Announcement {self.title}>'
