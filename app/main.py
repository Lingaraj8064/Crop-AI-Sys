"""
Crop Disease Detection System - Flask Application
Main application entry point with comprehensive agricultural AI features
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import uuid
from datetime import datetime
import numpy as np
from PIL import Image
import cv2
import random

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'crop-disease-detection-2024'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///crop_disease.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Models
class AnalysisResult(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = db.Column(db.String(255), nullable=False)
    plant_name = db.Column(db.String(100), nullable=False)
    disease_name = db.Column(db.String(100), nullable=True)
    is_healthy = db.Column(db.Boolean, default=False)
    confidence = db.Column(db.Float, nullable=False)
    analysis_data = db.Column(db.Text)  # JSON string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class ChatSession(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), nullable=False)
    messages = db.Column(db.Text)  # JSON string
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# Comprehensive Plant Database
PLANT_DATABASE = {
    "apple": {
        "name": "Apple",
        "scientific_name": "Malus domestica",
        "diseases": {
            "apple_scab": {
                "name": "Apple Scab",
                "severity": "High",
                "symptoms": "Dark, scaly lesions on leaves and fruit, premature leaf drop, reduced fruit quality",
                "causes": "Fungal infection caused by Venturia inaequalis, thrives in cool, moist conditions",
                "prevention": [
                    "Plant resistant apple varieties",
                    "Ensure proper air circulation by pruning",
                    "Remove fallen leaves and debris",
                    "Apply preventive fungicides in early spring"
                ],
                "treatment": [
                    "Apply copper-based fungicides",
                    "Use systemic fungicides like myclobutanil",
                    "Remove infected plant parts immediately",
                    "Improve orchard sanitation practices"
                ],
                "immediate_action": "Remove infected leaves and apply fungicide treatment immediately to prevent spread"
            },
            "fire_blight": {
                "name": "Fire Blight",
                "severity": "Critical",
                "symptoms": "Blackened, wilted shoots that look burned, cankers on branches, bacterial ooze",
                "causes": "Bacterial infection by Erwinia amylovora, spread by insects, rain, and wind",
                "prevention": [
                    "Avoid excessive nitrogen fertilization",
                    "Prune during dormant season",
                    "Use copper sprays during bloom",
                    "Plant resistant varieties"
                ],
                "treatment": [
                    "Prune infected branches 12 inches below symptoms",
                    "Apply streptomycin or oxytetracycline antibiotics",
                    "Disinfect pruning tools between cuts",
                    "Remove severely infected trees"
                ],
                "immediate_action": "Prune infected areas immediately and apply antibiotic treatment to save the tree"
            }
        },
        "healthy_info": {
            "care_tips": [
                "Water deeply but infrequently to encourage deep root growth",
                "Mulch around base to retain moisture and suppress weeds",
                "Prune annually during dormant season for shape and health",
                "Monitor for pest and disease signs regularly"
            ],
            "harvesting": "Harvest when apples are firm, fully colored, and easily separate from branch with a twist",
            "nutrition": "Apply balanced fertilizer in early spring, supplement with compost annually"
        },
        "soil_conditions": {
            "ph_range": "6.0-7.0",
            "drainage": "Well-draining, loamy soil",
            "nutrients": "Rich in organic matter, adequate phosphorus and potassium",
            "depth": "Minimum 3 feet for proper root development"
        },
        "weather_conditions": {
            "temperature": "Requires 400-1000 chill hours below 45°F, growing season 60-75°F",
            "rainfall": "25-40 inches annually, avoid waterlogged conditions",
            "humidity": "Moderate humidity, good air circulation essential",
            "sunlight": "Full sun (6-8 hours daily) for optimal fruit development"
        },
        "suitable_regions": [
            "USDA Zones 3-8",
            "Temperate climates with distinct seasons",
            "Regions with adequate winter chill hours",
            "Areas with moderate rainfall and good drainage"
        ]
    },
    "tomato": {
        "name": "Tomato",
        "scientific_name": "Solanum lycopersicum",
        "diseases": {
            "early_blight": {
                "name": "Early Blight",
                "severity": "Medium",
                "symptoms": "Dark brown spots with concentric rings on older leaves, yellowing and leaf drop",
                "causes": "Fungal infection by Alternaria solani, favored by warm, humid conditions",
                "prevention": [
                    "Rotate crops annually to break disease cycle",
                    "Space plants adequately for air circulation",
                    "Water at soil level, avoid wetting foliage",
                    "Apply mulch to prevent soil splash on leaves"
                ],
                "treatment": [
                    "Apply copper-based or chlorothalonil fungicides",
                    "Remove infected lower leaves immediately",
                    "Improve air circulation around plants",
                    "Use drip irrigation instead of overhead watering"
                ],
                "immediate_action": "Remove affected leaves and apply fungicide to prevent further spread"
            },
            "late_blight": {
                "name": "Late Blight",
                "severity": "Critical",
                "symptoms": "Water-soaked lesions on leaves, white fuzzy growth on undersides, fruit rot",
                "causes": "Oomycete pathogen Phytophthora infestans, spreads rapidly in cool, wet conditions",
                "prevention": [
                    "Plant certified disease-free seedlings",
                    "Ensure excellent drainage and air circulation",
                    "Apply preventive fungicides in high-risk periods",
                    "Monitor weather conditions closely"
                ],
                "treatment": [
                    "Apply systemic fungicides like metalaxyl",
                    "Remove and destroy infected plants immediately",
                    "Avoid overhead watering completely",
                    "Harvest green fruit before disease spreads"
                ],
                "immediate_action": "Emergency fungicide application and removal of infected plants to prevent total crop loss"
            }
        },
        "healthy_info": {
            "care_tips": [
                "Provide consistent moisture, avoid water stress",
                "Support plants with stakes or cages",
                "Prune suckers for better air circulation",
                "Side-dress with compost mid-season"
            ],
            "harvesting": "Harvest when fruits show first blush of color, ripen indoors if needed",
            "nutrition": "High nitrogen needs early, switch to phosphorus-potassium during fruiting"
        },
        "soil_conditions": {
            "ph_range": "6.0-6.8",
            "drainage": "Well-draining, fertile soil rich in organic matter",
            "nutrients": "High nitrogen initially, balanced NPK during fruiting",
            "depth": "18-24 inches for adequate root development"
        },
        "weather_conditions": {
            "temperature": "65-75°F optimal, sensitive to frost",
            "rainfall": "1-2 inches weekly, consistent moisture critical",
            "humidity": "Moderate humidity with good air circulation",
            "sunlight": "6-8 hours direct sunlight daily"
        },
        "suitable_regions": [
            "USDA Zones 2-11 as annual",
            "Warm season crop in temperate climates",
            "Greenhouse growing in cold regions",
            "Mediterranean and subtropical climates ideal"
        ]
    },
    "corn": {
        "name": "Corn",
        "scientific_name": "Zea mays",
        "diseases": {
            "corn_smut": {
                "name": "Corn Smut",
                "severity": "Medium",
                "symptoms": "Large, grayish-white galls on ears, stalks, and leaves",
                "causes": "Fungal infection by Ustilago maydis, enters through wounds",
                "prevention": [
                    "Avoid mechanical damage to plants",
                    "Control corn borers and other insects",
                    "Practice crop rotation",
                    "Remove infected galls before spores mature"
                ],
                "treatment": [
                    "Remove and destroy infected galls immediately",
                    "No effective chemical treatment available",
                    "Focus on prevention and sanitation",
                    "Harvest unaffected portions normally"
                ],
                "immediate_action": "Remove infected galls before they release black spores"
            },
            "northern_leaf_blight": {
                "name": "Northern Leaf Blight",
                "severity": "High",
                "symptoms": "Long, elliptical, gray-green lesions on leaves",
                "causes": "Fungal pathogen Exserohilum turcicum, favored by moderate temperatures and humidity",
                "prevention": [
                    "Plant resistant corn hybrids",
                    "Rotate with non-grass crops",
                    "Bury crop residue completely",
                    "Ensure adequate plant spacing"
                ],
                "treatment": [
                    "Apply triazole or strobilurin fungicides",
                    "Time applications at early symptom development",
                    "Multiple applications may be needed",
                    "Focus on protecting upper leaves"
                ],
                "immediate_action": "Apply fungicide treatment at first sign of lesions to protect yield"
            }
        },
        "healthy_info": {
            "care_tips": [
                "Plant in blocks for better pollination",
                "Hill soil around base for support",
                "Deep, infrequent watering preferred",
                "Side-dress with nitrogen at knee-high stage"
            ],
            "harvesting": "Sweet corn ready when silks are brown and kernels milky when punctured",
            "nutrition": "Heavy nitrogen feeder, requires adequate phosphorus and potassium"
        },
        "soil_conditions": {
            "ph_range": "6.0-6.8",
            "drainage": "Well-draining, deep, fertile soil",
            "nutrients": "High nitrogen requirements, adequate phosphorus and potassium",
            "depth": "Deep soil preferred for extensive root system"
        },
        "weather_conditions": {
            "temperature": "60-95°F growing range, 70-75°F optimal",
            "rainfall": "20-30 inches during growing season",
            "humidity": "Moderate humidity, avoid excessive moisture",
            "sunlight": "Full sun essential for maximum yield"
        },
        "suitable_regions": [
            "USDA Zones 3-11",
            "Corn Belt states ideal",
            "Areas with warm summers and adequate rainfall",
            "Plains and prairie regions excellent"
        ]
    }
}

# Chatbot Knowledge Base
CHATBOT_RESPONSES = {
    "greetings": [
        "Hello! I'm your agricultural AI assistant. How can I help you with your crops today?",
        "Welcome! I'm here to assist with all your farming and crop questions.",
        "Hi there! Ready to discuss agriculture, crops, or plant diseases?"
    ],
    "disease_symptoms": {
        "keywords": ["symptoms", "signs", "disease", "problem", "sick", "infected"],
        "response": "I can help identify disease symptoms! Common signs include discolored leaves, spots, wilting, unusual growths, or stunted development. Can you describe what you're seeing on your plants?"
    },
    "soil_management": {
        "keywords": ["soil", "pH", "fertilizer", "nutrients", "compost"],
        "response": "Soil health is crucial for crop success! Most crops prefer pH 6.0-7.0, well-draining soil rich in organic matter. Regular soil testing helps determine nutrient needs. What specific soil questions do you have?"
    },
    "weather_irrigation": {
        "keywords": ["water", "irrigation", "rainfall", "drought", "watering"],
        "response": "Proper irrigation is essential for healthy crops. Most plants need 1-2 inches of water weekly. Deep, infrequent watering encourages root development. Consider drip irrigation for efficiency. What watering challenges are you facing?"
    },
    "pest_management": {
        "keywords": ["pest", "insect", "bug", "aphid", "control"],
        "response": "Integrated pest management combines prevention, biological control, and targeted treatments. Regular monitoring helps catch problems early. Many beneficial insects help control pests naturally. What pests are you dealing with?"
    },
    "organic_farming": {
        "keywords": ["organic", "natural", "chemical-free", "sustainable"],
        "response": "Organic farming focuses on soil health, biodiversity, and natural pest control. Composting, crop rotation, and beneficial insects are key strategies. It takes time to transition but builds long-term soil fertility. Are you interested in organic methods?"
    },
    "harvesting": {
        "keywords": ["harvest", "picking", "ready", "ripe", "storage"],
        "response": "Harvest timing affects both quality and storage life. Each crop has specific indicators of ripeness. Proper post-harvest handling maintains quality. What crops are you looking to harvest?"
    }
}

def allowed_file(filename):
    """Check if uploaded file is allowed"""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def simulate_ai_analysis(image_path):
    """Simulate AI disease detection analysis"""
    # Randomly select a plant and condition for demo
    plant_keys = list(PLANT_DATABASE.keys())
    selected_plant = random.choice(plant_keys)
    plant_data = PLANT_DATABASE[selected_plant]
    
    # 70% chance of disease, 30% chance of healthy
    is_healthy = random.random() < 0.3
    confidence = round(random.uniform(85, 98), 1)
    
    result = {
        "plant_name": plant_data["name"],
        "scientific_name": plant_data["scientific_name"],
        "is_healthy": is_healthy,
        "confidence": confidence,
        "soil_conditions": plant_data["soil_conditions"],
        "weather_conditions": plant_data["weather_conditions"],
        "suitable_regions": plant_data["suitable_regions"]
    }
    
    if is_healthy:
        result.update({
            "status": "Healthy",
            "health_info": plant_data["healthy_info"]
        })
    else:
        # Select random disease
        disease_keys = list(plant_data["diseases"].keys())
        selected_disease = random.choice(disease_keys)
        disease_data = plant_data["diseases"][selected_disease]
        
        result.update({
            "disease_name": disease_data["name"],
            "severity": disease_data["severity"],
            "symptoms": disease_data["symptoms"],
            "causes": disease_data["causes"],
            "prevention": disease_data["prevention"],
            "treatment": disease_data["treatment"],
            "immediate_action": disease_data["immediate_action"]
        })
    
    return result

def get_chatbot_response(user_message):
    """Generate chatbot response based on user input"""
    user_message_lower = user_message.lower()
    
    # Check for greetings
    if any(word in user_message_lower for word in ["hello", "hi", "hey", "greetings"]):
        return random.choice(CHATBOT_RESPONSES["greetings"])
    
    # Check for specific topics
    for topic, data in CHATBOT_RESPONSES.items():
        if topic == "greetings":
            continue
        
        if any(keyword in user_message_lower for keyword in data["keywords"]):
            return data["response"]
    
    # Default response for unmatched queries
    return "I'm here to help with agricultural questions! You can ask me about crop diseases, soil management, irrigation, pest control, organic farming, or harvesting techniques. What would you like to know?"

# Routes
@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_image():
    """Handle image upload and analysis"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
        filename = timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Simulate AI analysis
        analysis_result = simulate_ai_analysis(file_path)
        
        # Save to database
        result_id = str(uuid.uuid4())
        db_result = AnalysisResult(
            id=result_id,
            filename=filename,
            plant_name=analysis_result['plant_name'],
            disease_name=analysis_result.get('disease_name'),
            is_healthy=analysis_result['is_healthy'],
            confidence=analysis_result['confidence'],
            analysis_data=json.dumps(analysis_result)
        )
        db.session.add(db_result)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'result_id': result_id,
            'analysis': analysis_result,
            'image_url': f'/static/uploads/{filename}'
        })
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chatbot interactions"""
    data = request.get_json()
    user_message = data.get('message', '')
    session_id = data.get('session_id', str(uuid.uuid4()))
    
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Generate response
    bot_response = get_chatbot_response(user_message)
    
    # Save chat session
    chat_session = ChatSession(
        session_id=session_id,
        messages=json.dumps({
            'user': user_message,
            'bot': bot_response,
            'timestamp': datetime.utcnow().isoformat()
        })
    )
    db.session.add(chat_session)
    db.session.commit()
    
    return jsonify({
        'response': bot_response,
        'session_id': session_id
    })

@app.route('/results/<result_id>')
def get_results(result_id):
    """Get analysis results by ID"""
    result = AnalysisResult.query.get_or_404(result_id)
    analysis_data = json.loads(result.analysis_data)
    
    return jsonify({
        'id': result.id,
        'filename': result.filename,
        'analysis': analysis_data,
        'timestamp': result.timestamp.isoformat(),
        'image_url': f'/static/uploads/{result.filename}'
    })

@app.route('/api/plants')
def get_plants():
    """Get all plants in database"""
    plants = []
    for key, plant_data in PLANT_DATABASE.items():
        plants.append({
            'id': key,
            'name': plant_data['name'],
            'scientific_name': plant_data['scientific_name'],
            'diseases': list(plant_data['diseases'].keys())
        })
    return jsonify({'plants': plants})

@app.route('/api/plant/<plant_id>')
def get_plant_info(plant_id):
    """Get detailed plant information"""
    if plant_id not in PLANT_DATABASE:
        return jsonify({'error': 'Plant not found'}), 404
    
    return jsonify(PLANT_DATABASE[plant_id])

@app.route('/api/history')
def get_analysis_history():
    """Get recent analysis history"""
    results = AnalysisResult.query.order_by(AnalysisResult.timestamp.desc()).limit(10).all()
    history = []
    
    for result in results:
        history.append({
            'id': result.id,
            'plant_name': result.plant_name,
            'disease_name': result.disease_name,
            'is_healthy': result.is_healthy,
            'confidence': result.confidence,
            'timestamp': result.timestamp.isoformat(),
            'image_url': f'/static/uploads/{result.filename}'
        })
    
    return jsonify({'history': history})

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(413)
def too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413

# Initialize database tables
def init_db():
    """Initialize database tables"""
    db.create_all()

if __name__ == '__main__':
    # Create tables on first run
    with app.app_context():
        init_db()
    
    app.run(debug=True, host='0.0.0.0', port=5000)