# Corps Attendance Face Recognition System

A comprehensive web-based attendance tracking system designed for NYSC Corps Members using facial recognition technology and PIN verification for enhanced security.

## Features

- **Dual Authentication**: Face recognition + PIN verification for maximum security
- **Location-Based Attendance**: Admin-controlled daily location scheduling
- **Real-time Recognition**: Auto-detect camera with live face recognition
- **Comprehensive Dashboard**: User and admin dashboards with attendance analytics
- **Notification System**: Email and SMS notifications for attendance events
- **Attendance Reports**: Detailed reports and analytics
- **Priority Announcements**: Admin announcements with priority levels for important notices
- **Mobile Responsive**: Works on all devices
- **Secure**: Account lockouts, password hashing, session management

## Technical Stack

- **Backend**: Flask (Python)
- **Database**: SQLite (development) / PostgreSQL (production)
- **Face Recognition**: OpenCV + face_recognition library
- **Frontend**: Bootstrap 5, HTML5, JavaScript
- **Notifications**: Flask-Mail + Twilio SMS
- **Deployment**: Heroku ready with Gunicorn

## Quick Start

### Prerequisites

- Python 3.11+
- Webcam/Camera for face recognition
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone [repository-url]
   cd corps_attendance_system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   # Copy example environment file
   cp .env.example .env
   # Edit .env with your configurations
   ```

5. **Initialize database**
   ```bash
   python create_db.py
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Access the application**
   - Open browser to `http://localhost:5000`
   - Admin login: `admin@corps.gov.ng` / `admin123` / PIN: `0000`

## Environment Configuration

### Required Environment Variables

```env
# Flask Configuration
SECRET_KEY=your-super-secret-key-here
FLASK_ENV=development

# Database
DATABASE_URL=sqlite:///corps_attendance.db

# Email Configuration (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=admin@corps.gov.ng

# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

### Optional Configuration

```env
# Face Recognition Settings
FACE_RECOGNITION_TOLERANCE=0.6
MAX_FACE_DISTANCE=0.4

# Security
JWT_SECRET_KEY=your-jwt-secret-key

# File Upload
MAX_CONTENT_LENGTH=16777216
```

## Usage Guide

### For Corps Members

1. **Registration**
   - Visit `/auth/register`
   - Fill personal details (State Code, Name, Email, etc.)
   - Upload a clear face photo
   - Set password and 4-digit PIN
   - Verify email if enabled

2. **Daily Attendance**
   - Visit `/attendance`
   - Enter State Code and PIN
   - Look at camera for face recognition
   - Both face and PIN must match for attendance to be recorded

3. **View History**
   - Access personal dashboard
   - View attendance history and statistics
   - Download attendance reports

### For Administrators

1. **Location Management**
   - Add/edit CD locations
   - Set camera configurations
   - Manage location capacity and details

2. **Schedule Management**
   - Set daily CD schedules
   - Activate specific locations for attendance
   - Configure time windows and expected attendees

3. **User Management**
   - View all registered corps members
   - Activate/deactivate accounts
   - Reset passwords and PINs
   - View individual attendance records

4. **Reports & Analytics**
   - Daily attendance summaries
   - Location-wise attendance reports
   - Export data for analysis
   - Monitor attendance trends

5. **Announcements Management**
   - Create system-wide announcements
   - Set priority levels (Low, Medium, High, Critical)
   - Schedule announcements for specific dates
   - Track announcement visibility and engagement

## Deployment

### Heroku Deployment

1. **Install Heroku CLI**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login and create app**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Add PostgreSQL addon**
   ```bash
   heroku addons:create heroku-postgresql:hobby-dev
   ```

4. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY=your-secret-key
   heroku config:set FLASK_CONFIG=production
   # Add other required variables
   ```

5. **Deploy**
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push heroku main
   ```

6. **Initialize database**
   ```bash
   heroku run flask deploy
   ```

### Local Development

1. **Run in debug mode**
   ```bash
   export FLASK_ENV=development
   python run.py
   ```

2. **Database migrations**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

3. **Recent Updates**
   - Added priority system to announcements (v1.1)
   - Enhanced admin dashboard with announcement management
   - Improved notification system with priority-based alerts

## Camera Setup

### Auto-Detection
The system automatically detects available cameras. For multiple cameras:

1. **Check available cameras**
   ```python
   import cv2
   for i in range(10):
       cap = cv2.VideoCapture(i)
       if cap.isOpened():
           print(f"Camera {i} is available")
       cap.release()
   ```

2. **Configure specific camera**
   - Update camera_id in location settings
   - Test camera functionality in admin panel

### Camera Requirements
- Resolution: Minimum 640x480
- Position: Face-level, good lighting
- Distance: 50-100cm from user
- Stability: Stable mounting recommended

## Face Recognition Setup

### Image Requirements
- **Format**: JPG, PNG
- **Size**: Maximum 16MB
- **Quality**: High resolution, clear face
- **Lighting**: Good natural or artificial light
- **Angle**: Front-facing, minimal tilt
- **Background**: Clean, non-cluttered

### Optimization Tips
- Use consistent lighting at registration and attendance
- Ensure camera is at eye level
- Allow face recognition service to retrain periodically
- Clean camera lens regularly

## Security Features

### Authentication
- **Dual Factor**: Face + PIN required
- **Account Lockout**: 5 failed attempts = 30-minute lock
- **Password Hashing**: Werkzeug PBKDF2
- **Session Management**: Flask-Login sessions

### Data Protection
- **Face Data**: Encrypted JSON storage
- **Database**: SQL injection protection
- **File Upload**: Secure filename handling
- **CSRF Protection**: Flask-WTF tokens

### Privacy
- **Face Images**: Stored locally, not shared
- **User Data**: Minimal collection, encrypted storage
- **Logging**: Security events logged
- **Access Control**: Role-based permissions

## API Documentation

### Authentication Required
All API endpoints require authentication.

### Endpoints

#### Mark Attendance
```http
POST /api/attendance/mark
Content-Type: application/json

{
  "state_code": "NY/23A/1234",
  "pin": "1234",
  "location_id": 1
}
```

#### Get User History
```http
GET /api/attendance/history?days=30
```

#### Get Location Summary
```http
GET /api/location/1/summary?date=2024-07-21
```

## Troubleshooting

### Common Issues

1. **Camera Not Detected**
   - Check camera permissions
   - Try different camera index
   - Restart application

2. **Face Recognition Fails**
   - Ensure good lighting
   - Check face image quality
   - Retrain face encodings

3. **Database Errors**
   - Check database connection
   - Run migrations
   - Restart application

4. **Email/SMS Not Working**
   - Verify credentials
   - Check network connectivity
   - Review service quotas

### Error Logs
Check `logs/corps_attendance.log` for detailed error information.

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## Support

For support and questions:
- Create an issue on GitHub
- Email: support@yourdomain.com
- Documentation: [Wiki Link]

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- NYSC for inspiration and requirements
- OpenCV and face_recognition library contributors
- Flask community and contributors
- Bootstrap team for the UI framework

---

**Built with ❤️ for Nigerian Corps Members**
