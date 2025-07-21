import os
from app import create_app, db
from app.models import User, Attendance, Location, CDSchedule
from flask_migrate import upgrade
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = create_app(os.environ.get('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'User': User, 
        'Attendance': Attendance, 
        'Location': Location,
        'CDSchedule': CDSchedule
    }

@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # Migrate database to latest revision
    upgrade()
    
    # Create default admin user if not exists
    create_default_admin()

def create_default_admin():
    """Create default admin user"""
    admin = User.query.filter_by(email='admin@corps.gov.ng').first()
    if not admin:
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
        db.session.commit()
        print("Default admin user created!")

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') == 'development')
