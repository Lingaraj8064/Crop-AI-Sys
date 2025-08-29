"""
Crop Disease Detection System - Application Runner
This is the main entry point to start the Flask application
Place this file in the ROOT DIRECTORY of your project
"""

import os
from dotenv import load_dotenv
from app.main import app, db

# Load environment variables
load_dotenv()

def create_tables():
    """Create database tables if they don't exist"""
    with app.app_context():
        db.create_all()
        print("✅ Database tables created successfully!")

def main():
    """Main function to run the application"""
    print("🌾 Starting Crop Disease Detection System...")
    print("🚀 Initializing Flask application...")
    
    # Create database tables
    create_tables()
    
    # Get configuration from environment variables
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', 5000))
    
    print(f"🌐 Server will run on: http://{host}:{port}")
    print("📱 Access the application in your web browser")
    print("🤖 AI Disease Detection & Agricultural Assistant Ready!")
    print("=" * 50)
    
    # Run the Flask application
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        use_reloader=True
    )

if __name__ == '__main__':
    main()