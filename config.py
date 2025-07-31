import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database configuration
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or \
        f"postgresql://{os.environ.get('DB_USER', 'username')}:" \
        f"{os.environ.get('DB_PASSWORD', 'password')}@" \
        f"{os.environ.get('DB_HOST', 'localhost')}:" \
        f"{os.environ.get('DB_PORT', '5432')}/" \
        f"{os.environ.get('DB_NAME', 'mkulima_smart')}"
    
    # LLM Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    LANGCHAIN_API_KEY = os.environ.get('LANGCHAIN_API_KEY')
    LANGCHAIN_TRACING_V2 = os.environ.get('LANGCHAIN_TRACING_V2', 'false').lower() == 'true'
    LANGCHAIN_PROJECT = os.environ.get('LANGCHAIN_PROJECT', 'mkulima_smart')
    
    # Africa's Talking Configuration
    AFRICASTALKING_USERNAME = os.environ.get('AFRICASTALKING_USERNAME', 'sandbox')
    AFRICASTALKING_API_KEY = os.environ.get('AFRICASTALKING_API_KEY')
    
    # Application settings
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = 'production'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
