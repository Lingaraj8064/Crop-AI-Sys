"""
Crop Disease Detection System - Flask Application Package
Initialize Flask application with all extensions and configurations
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

# Initialize extensions
db = SQLAlchemy()
cors = CORS()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Load configuration
    from app.config import Config
    app.config.from_object(Config)
    
    # Initialize extensions
    db.init_app(app)
    cors.init_app(app)
    
    # Register blueprints/routes
    from app.routes import main_routes, upload_routes, api_routes, chatbot_routes
    app.register_blueprint(main_routes.bp)
    app.register_blueprint(upload_routes.bp)
    app.register_blueprint(api_routes.bp)
    app.register_blueprint(chatbot_routes.bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Ensure upload directory exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/uploads'), exist_ok=True)
    
    return app