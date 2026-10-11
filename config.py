import os

class Config:
    """Base configuration for the Healthcare Record Management application."""
    # Secret key for server-side session signing and CSRF security
    SECRET_KEY = os.environ.get('SECRET_KEY', 'healthcare-secure-college-demo-key-2026')
    
    # Database connection URI
    # Defaults to local SQLite for simplicity; override via DATABASE_URL in cloud environments
    raw_db_url = os.environ.get('DATABASE_URL', 'sqlite:///healthcare.db')
    # Compatibility fix for cloud services providing postgres:// instead of postgresql://
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session cookie security settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # Set to True in production when served over HTTPS
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
