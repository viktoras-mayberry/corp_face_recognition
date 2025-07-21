import os
from datetime import timedelta

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///corps_attendance.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Face Recognition Settings
    FACE_RECOGNITION_TOLERANCE = float(os.environ.get('FACE_RECOGNITION_TOLERANCE', 0.6))
    MAX_FACE_DISTANCE = float(os.environ.get('MAX_FACE_DISTANCE', 0.4))
    
    # File Upload Settings
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'data', 'uploads')
    FACES_FOLDER = os.path.join(os.getcwd(), 'data', 'faces')
    ENCODINGS_FOLDER = os.path.join(os.getcwd(), 'data', 'encodings')
    UNKNOWN_FACES_FOLDER = os.path.join(os.getcwd(), 'data', 'unknown_faces')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    # Security
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-string-change-in-production'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    WTF_CSRF_ENABLED = True
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@corps.gov.ng')
    
    # SMS Configuration (Twilio)
    TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')
    
    # Attendance Settings
    ATTENDANCE_START_TIME = "08:00"  # 8:00 AM
    LATE_THRESHOLD = "08:30"         # 8:30 AM
    VERY_LATE_THRESHOLD = "09:00"    # 9:00 AM
    
    # Pagination
    POSTS_PER_PAGE = 25
    
    # Logging
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Redis Configuration
    REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    
    # Celery Configuration
    CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
    CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://localhost:6379')

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.getcwd(), 'corps_attendance_dev.db')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
    # Use PostgreSQL in production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.getcwd(), 'corps_attendance.db')
    
    # Fix for Heroku Postgres URL
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)

class HerokuConfig(ProductionConfig):
    SSL_DISABLE = bool(os.environ.get('SSL_DISABLE'))

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'heroku': HerokuConfig,
    'default': DevelopmentConfig
}
