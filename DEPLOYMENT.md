# Corps Attendance System - Deployment Guide

## Quick Deployment Checklist

### 1. Pre-deployment Setup

- [ ] Create `.env` file from `.env.example`
- [ ] Update environment variables with production values
- [ ] Test application locally
- [ ] Ensure all dependencies are in `requirements.txt`

### 2. Local Development

```bash
# Clone repository
git clone <repository-url>
cd corps_attendance_system

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python create_db.py

# Run application
python run.py
```

### 3. Heroku Deployment

#### Prerequisites
- Heroku CLI installed
- Git repository initialized

#### Steps
```bash
# Login to Heroku
heroku login

# Create Heroku app
heroku create your-app-name

# Add PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev

# Set environment variables
heroku config:set SECRET_KEY=your-production-secret-key
heroku config:set FLASK_CONFIG=heroku
heroku config:set MAIL_USERNAME=your-email@gmail.com
heroku config:set MAIL_PASSWORD=your-gmail-app-password
# Add other environment variables as needed

# Deploy to Heroku
git add .
git commit -m "Initial deployment"
git push heroku master

# Initialize database
heroku run flask deploy
```

#### Important Heroku Configuration

The following files are configured for Heroku deployment:
- `Procfile`: Defines web and release processes
- `runtime.txt`: Specifies Python version
- `requirements.txt`: Lists all dependencies

### 4. Production Environment Variables

Required environment variables for production:

```env
# Core Configuration
SECRET_KEY=your-super-secure-secret-key
FLASK_CONFIG=production
DATABASE_URL=postgresql://user:password@host:port/database

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-email-app-password
ADMIN_EMAIL=admin@yourdomain.com

# SMS Configuration (Optional)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# Security
JWT_SECRET_KEY=your-jwt-secret-key
WTF_CSRF_ENABLED=True

# Monitoring (Optional)
SENTRY_DSN=your-sentry-dsn
```

### 5. Database Setup

#### For SQLite (Development)
```bash
python create_db.py
```

#### For PostgreSQL (Production)
```bash
# Set DATABASE_URL environment variable
export DATABASE_URL=postgresql://user:password@host:port/database

# Run migrations
flask db upgrade

# Create default admin user
flask deploy
```

### 6. Post-Deployment Verification

- [ ] Application loads without errors
- [ ] Database is accessible and populated
- [ ] Admin login works (admin@corps.gov.ng / admin123 / PIN: 0000)
- [ ] Face recognition system initializes properly
- [ ] Email notifications work (if configured)
- [ ] File uploads work correctly

### 7. Security Considerations

#### Production Security Checklist
- [ ] Change default admin credentials
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS
- [ ] Configure firewall rules
- [ ] Regularly update dependencies
- [ ] Monitor application logs
- [ ] Backup database regularly

#### Face Recognition Security
- [ ] Face images stored locally only
- [ ] Face encodings encrypted in database
- [ ] Secure file upload validation
- [ ] Regular cleanup of temporary files

### 8. Monitoring and Maintenance

#### Log Files
- Application logs: `logs/corps_attendance.log`
- Error tracking via Sentry (if configured)

#### Database Backups
```bash
# Heroku PostgreSQL backup
heroku pg:backups:capture
heroku pg:backups:download
```

#### Performance Monitoring
- Monitor database performance
- Track face recognition accuracy
- Monitor file storage usage
- Check email delivery rates

### 9. Troubleshooting

#### Common Issues

**Database Connection Error**
```bash
# Check DATABASE_URL
echo $DATABASE_URL

# Test database connection
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); print(db.engine.execute('SELECT 1').scalar())"
```

**Face Recognition Issues**
- Ensure camera permissions are granted
- Check lighting conditions
- Verify face image quality
- Clear face encodings cache if needed

**Email Not Working**
- Verify SMTP credentials
- Check Gmail app password setup
- Confirm firewall settings
- Test with different email provider

#### Support
- Check application logs first
- Review environment variables
- Test with minimal configuration
- Contact development team with specific error messages

## Environment-Specific Notes

### Development
- Uses SQLite database
- Debug mode enabled
- Detailed error messages
- Face recognition in simplified mode

### Production
- Uses PostgreSQL database
- Debug mode disabled
- Error logging to files
- Full face recognition capabilities
- HTTPS recommended
- Environment variable validation

### Testing
- In-memory SQLite database
- CSRF protection disabled
- Simplified authentication
- Mock external services
