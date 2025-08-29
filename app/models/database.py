"""
Crop Disease Detection System - Database Models
SQLAlchemy models for data persistence
"""

from app import db
from datetime import datetime
import uuid
import json

class AnalysisResult(db.Model):
    """Model for storing crop disease analysis results"""
    __tablename__ = 'analysis_results'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    
    # Plant identification results
    plant_id = db.Column(db.String(36), db.ForeignKey('plant_species.id'), nullable=True)
    plant_name = db.Column(db.String(100), nullable=False)
    scientific_name = db.Column(db.String(150))
    
    # Disease detection results
    disease_id = db.Column(db.String(36), db.ForeignKey('diseases.id'), nullable=True)
    disease_name = db.Column(db.String(100), nullable=True)
    is_healthy = db.Column(db.Boolean, default=False)
    confidence = db.Column(db.Float, nullable=False)
    severity_level = db.Column(db.String(20))  # Low, Medium, High, Critical
    
    # Analysis metadata
    analysis_data = db.Column(db.Text)  # JSON string with detailed results
    processing_time = db.Column(db.Float)  # Processing time in seconds
    model_version = db.Column(db.String(20))
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_ip = db.Column(db.String(45))  # Support IPv6
    user_agent = db.Column(db.Text)
    
    # Relationships
    plant = db.relationship('PlantSpecies', backref='analysis_results', lazy=True)
    disease = db.relationship('Disease', backref='analysis_results', lazy=True)
    
    def __repr__(self):
        return f'<AnalysisResult {self.plant_name} - {self.disease_name or "Healthy"}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'filename': self.filename,
            'plant_name': self.plant_name,
            'disease_name': self.disease_name,
            'is_healthy': self.is_healthy,
            'confidence': self.confidence,
            'severity_level': self.severity_level,
            'analysis_data': json.loads(self.analysis_data) if self.analysis_data else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'image_url': f'/static/uploads/{self.filename}'
        }

class ChatSession(db.Model):
    """Model for storing chatbot conversations"""
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), nullable=False, index=True)
    
    # Message content
    user_message = db.Column(db.Text, nullable=False)
    bot_response = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(50), default='general')  # general, disease, soil, etc.
    
    # Context and metadata
    context_data = db.Column(db.Text)  # JSON string with conversation context
    confidence_score = db.Column(db.Float)
    response_time = db.Column(db.Float)  # Response generation time
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_ip = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    def __repr__(self):
        return f'<ChatSession {self.session_id}>'
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'user_message': self.user_message,
            'bot_response': self.bot_response,
            'message_type': self.message_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class User(db.Model):
    """User model for authentication (future feature)"""
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    
    # Profile information
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    farm_name = db.Column(db.String(100))
    location = db.Column(db.String(100))
    farm_size = db.Column(db.Float)  # in acres
    primary_crops = db.Column(db.Text)  # JSON array of crop types
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    email_verified = db.Column(db.Boolean, default=False)
    
    # Audit fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<User {self.username}>'

class PlantSpecies(db.Model):
    """Model for plant species information"""
    __tablename__ = 'plant_species'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    common_name = db.Column(db.String(100), nullable=False)
    scientific_name = db.Column(db.String(150), nullable=False)
    family = db.Column(db.String(100))
    category = db.Column(db.String(50))  # vegetable, fruit, grain, etc.
    
    # Growing information
    soil_requirements = db.Column(db.Text)  # JSON string
    weather_requirements = db.Column(db.Text)  # JSON string
    suitable_regions = db.Column(db.Text)  # JSON array
    growing_season = db.Column(db.String(100))
    harvest_time = db.Column(db.String(100))
    
    # Care information
    care_instructions = db.Column(db.Text)  # JSON string
    nutrition_needs = db.Column(db.Text)  # JSON string
    common_pests = db.Column(db.Text)  # JSON array
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PlantSpecies {self.common_name}>'

class Disease(db.Model):
    """Model for plant disease information"""
    __tablename__ = 'diseases'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    scientific_name = db.Column(db.String(150))
    type = db.Column(db.String(50))  # fungal, bacterial, viral, nutritional
    severity = db.Column(db.String(20))  # Low, Medium, High, Critical
    
    # Disease information
    symptoms = db.Column(db.Text, nullable=False)
    causes = db.Column(db.Text, nullable=False)
    affected_parts = db.Column(db.Text)  # JSON array: leaves, stems, fruits, etc.
    
    # Treatment and prevention
    treatment = db.Column(db.Text)  # JSON array of treatment steps
    prevention = db.Column(db.Text)  # JSON array of prevention methods
    immediate_action = db.Column(db.Text)
    organic_treatment = db.Column(db.Text)  # JSON array
    
    # Environmental factors
    favorable_conditions = db.Column(db.Text)  # JSON string
    spread_method = db.Column(db.String(100))
    contagious_level = db.Column(db.String(20))  # Low, Medium, High
    
    # Affected plants (many-to-many relationship)
    affected_plants = db.Column(db.Text)  # JSON array of plant IDs
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Disease {self.name}>'

class SystemLog(db.Model):
    """Model for system logging and monitoring"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    level = db.Column(db.String(20), nullable=False)  # INFO, WARNING, ERROR, CRITICAL
    message = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # upload, analysis, chat, system
    
    # Context information
    user_ip = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    request_id = db.Column(db.String(36))
    session_id = db.Column(db.String(36))
    
    # Additional data
    extra_data = db.Column(db.Text)  # JSON string
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemLog {self.level}: {self.message[:50]}>'