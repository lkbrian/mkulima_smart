import os
from flask import Flask
from flask_restful import Api
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import config
from models import db
from api.v1 import api_v1_bp

def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    jwt = JWTManager(app)
    CORS(app)
    
    # Register blueprints
    app.register_blueprint(api_v1_bp, url_prefix='/api/v1')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {
            "status": "healthy",
            "version": "1.0.0",
            "service": "mkulima-smart-api"
        }
    
    @app.route('/')
    def index():
        return {
            "message": "Mkulima Smart API",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "api_v1": "/api/v1",
                "docs": "/api/v1/docs"
            }
        }
    
    return app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    config_name = os.environ.get('FLASK_ENV', 'development')
    app_config = config[config_name]
    
    app.run(
        host=app_config.HOST,
        port=app_config.PORT,
        debug=app_config.DEBUG
    )
