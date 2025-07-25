from app import create_app, db
from app.models import User, Location, CDSchedule, Announcement
import os
from datetime import date, datetime

def create_database():
    """Create database and initial data"""
    app = create_app('development')
    
    with app.app_context():
        # Drop all tables first (for clean setup)
        db.drop_all()
        # Create all tables
        db.create_all()
        
        # Create admin user
        admin = User(
            state_code='ADMIN001',
            full_name='System Administrator',
            email='admin@corps.gov.ng',
            is_admin=True,
            is_active=True,
            email_verified=True
        )
        admin.set_password('admin123')
        admin.set_pin('0000')
        db.session.add(admin)
        
        # Create sample locations
        locations = [
            {
                'name': 'Lagos State Secretariat',
                'address': 'Alausa, Ikeja, Lagos',
                'local_government': 'Ikeja',
                'state': 'Lagos',
                'max_capacity': 100,
                'description': 'Main CD venue for Lagos State'
            },
            {
                'name': 'Abuja Municipal Area Council',
                'address': 'AMAC Headquarters, Abuja',
                'local_government': 'AMAC',
                'state': 'FCT',
                'max_capacity': 80,
                'description': 'CD venue for FCT corps members'
            },
            {
                'name': 'Rivers State Government House',
                'address': 'Government House, Port Harcourt',
                'local_government': 'Port Harcourt',
                'state': 'Rivers',
                'max_capacity': 120,
                'description': 'Main CD venue for Rivers State'
            }
        ]
        
        location_objects = []
        for loc_data in locations:
            location = Location(**loc_data)
            db.session.add(location)
            location_objects.append(location)
        
        # Commit locations first so they get IDs
        db.session.commit()
        
        # Create sample schedule for today
        for location in location_objects[:2]:  # Schedule first 2 locations for today
            schedule = CDSchedule(
                location_id=location.id,
                schedule_date=date.today(),
                start_time=datetime.strptime("08:00", "%H:%M").time(),
                end_time=datetime.strptime("16:00", "%H:%M").time(),
                activity_type="Community Development",
                description="Weekly CD activity",
                expected_attendees=50,
                is_active=True
            )
            db.session.add(schedule)
        
        # Create sample announcements
        announcements = [
            {
                'title': 'Welcome to NYSC CD Attendance System',
                'message': 'Welcome to the new digital attendance system! Please ensure you upload your face image in your profile to enable face recognition for easy attendance marking.',
                'announcement_type': 'info',
                'is_active': True,
                'is_urgent': False,
                'created_by': admin.id
            },
            {
                'title': 'CD Activity - Environmental Sanitation',
                'message': 'This Thursday, we will be participating in environmental sanitation activities. Please come prepared with appropriate clothing and tools. Meeting time: 7:00 AM.',
                'announcement_type': 'warning',
                'is_active': True,
                'is_urgent': True,
                'created_by': admin.id
            },
            {
                'title': 'Congratulations to Outstanding Corps Members',
                'message': 'We celebrate the corps members who have maintained 100% attendance this month. Keep up the excellent work!',
                'announcement_type': 'success',
                'is_active': True,
                'is_urgent': False,
                'created_by': admin.id
            }
        ]
        
        for announcement_data in announcements:
            announcement = Announcement(**announcement_data)
            db.session.add(announcement)
        
        db.session.commit()
        print("Database created successfully!")
        print("Admin credentials - Email: admin@corps.gov.ng, Password: admin123, PIN: 0000")
        print("Sample locations, schedules, and announcements created.")

if __name__ == '__main__':
    create_database()
