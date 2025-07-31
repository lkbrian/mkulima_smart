import os
from flask import Flask
from flask_restful import Api
from flask_cors import CORS
from config import config
from models import db
from resources import HealthCheckResource, FarmingTipsResource


def create_app(config_name=None):
    """Application factory pattern."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Create API
    api = Api(app)
    # Add SMS API resources
    api.add_resource(HealthCheckResource, "/health")
    api.add_resource(FarmingTipsResource, "/farming/tips")

    @app.route("/")
    def index():
        return {
            "message": "Mkulima Smart SMS API",
            "version": "1.0.0",
            "description": "SMS-based farming insights using Africa's Talking and Groq LLM",
            "endpoints": {"health": "/health", "farming_tips": "/farming/tips"},
        }

    # Create database tables
    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    config_name = os.environ.get("FLASK_ENV", "development")
    app_config = config[config_name]

    app.run(host=app_config.HOST, port=app_config.PORT, debug=app_config.DEBUG)
