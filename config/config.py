import os
from datetime import timedelta

class Config:
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'crimap-secret-key-2025')
    
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///crm.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Email Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'CRIMAP System <noreply@crimap.com>')
    
    # Intervention Settings
    INTERVENTION_EMAILS_ENABLED = True
    REMINDER_DAYS_BEFORE_DUE = [7, 3, 1]
    HIGH_RISK_ALERT_THRESHOLD = 0.7
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    
    # ML Model Settings
    ML_MODEL_PATH = 'ml_engine/models/xgb_model.pkl'
    RISK_THRESHOLD_HIGH = 0.7
    RISK_THRESHOLD_MEDIUM = 0.3

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}