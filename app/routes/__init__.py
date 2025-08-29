"""
Crop Disease Detection System - Routes Package
Blueprint registration for different route modules
"""

from app.routes import main_routes, upload_routes, api_routes, chatbot_routes

__all__ = [
    'main_routes',
    'upload_routes', 
    'api_routes',
    'chatbot_routes'
]