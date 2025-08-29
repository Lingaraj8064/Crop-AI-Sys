# 🌾 Crop Disease Detection System

A comprehensive AI-powered web application for crop disease detection and agricultural advisory services. This system helps farmers and agricultural professionals identify plant diseases, get treatment recommendations, and receive expert agricultural guidance through an intelligent chatbot.

## 🚀 Features

### 🔬 AI Disease Detection
- **Image Upload**: Drag-and-drop or click-to-browse interface
- **Plant Identification**: Automatic identification of crop species
- **Disease Detection**: AI-powered disease classification with confidence scores
- **Comprehensive Analysis**: Detailed information about symptoms, causes, and treatments

### 📊 Detailed Information Display
- **Disease Information**: Symptoms, severity levels, causes, and immediate actions
- **Treatment Recommendations**: Step-by-step treatment protocols
- **Prevention Strategies**: Preventive measures and best practices
- **Soil & Weather Requirements**: Optimal growing conditions
- **Regional Suitability**: Geographic growing recommendations

### 🤖 Intelligent Chatbot
- **Agricultural Expertise**: Knowledgeable about crops, diseases, soil, and weather
- **Real-time Assistance**: Instant responses to farming questions
- **Multi-topic Support**: Pest management, organic farming, harvesting, irrigation
- **Session Management**: Persistent chat history during sessions

### 📱 Modern User Experience
- **Responsive Design**: Mobile-first approach for all devices
- **Modern UI**: Glassmorphism effects and gradient backgrounds
- **Smooth Animations**: Professional transitions and loading states
- **Intuitive Interface**: User-friendly design for farmers and professionals

## 🛠️ Technology Stack

### Backend
- **Framework**: Python Flask 2.3.3
- **Database**: SQLAlchemy with SQLite (development) / PostgreSQL (production)
- **AI/ML**: TensorFlow 2.13.0, Keras, scikit-learn
- **Image Processing**: OpenCV, Pillow
- **API**: RESTful APIs with JSON responses

### Frontend
- **Languages**: HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Modern CSS with glassmorphism and gradients
- **Responsive**: Mobile-first design approach
- **Components**: Modular and reusable components

### Development & Deployment
- **Containerization**: Docker & Docker Compose
- **Environment Management**: python-dotenv
- **Testing**: pytest
- **Production Server**: Gunicorn

## 📁 Project Structure

```
crop_disease_detection_system/
├── app/                        # Flask application
│   ├── main.py                 # Application entry point
│   ├── models/                 # Database models
│   ├── routes/                 # Route handlers
│   ├── services/               # Business logic
│   └── utils/                  # Utility functions
├── static/                     # Static files (CSS, JS, images)
├── templates/                  # Jinja2 HTML templates
├── ml_models/                  # AI models and training scripts
├── database/                   # Database files and migrations
├── tests/                      # Unit and integration tests
├── docs/                       # Project documentation
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker configuration
├── docker-compose.yml          # Multi-container setup
├── .env.example               # Environment variables template
└── run.py                     # Main application runner
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- pip (Python package manager)
- Git

### Option 1: Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/crop-disease-detection-system.git
   cd crop-disease-detection-system
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

6. **Access the application**
   Open your browser and go to `http://127.0.0.1:5000`

### Option 2: Docker Setup

1. **Clone and navigate to project**
   ```bash
   git clone https://github.com/yourusername/crop-disease-detection-system.git
   cd crop-disease-detection-system
   ```

2. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   Open your browser and go to `http://localhost:5000`

## 📖 Usage Guide

### 🌿 Disease Detection

1. **Upload Image**: 
   - Drag and drop a leaf image or click to browse
   - Supported formats: JPG, PNG, GIF, BMP
   - Maximum file size: 16MB

2. **View Results**:
   - Plant species identification
   - Health status or disease name
   - Confidence percentage
   - Detailed analysis and recommendations

3. **Get Recommendations**:
   - Treatment protocols
   - Prevention strategies
   - Care instructions
   - Optimal growing conditions

### 💬 Chatbot Assistant

1. **Start Conversation**: Click the chat icon to open the assistant
2. **Ask Questions**: Type questions about crops, diseases, soil, or farming
3. **Get Expert Advice**: Receive detailed responses and recommendations
4. **Multi-topic Support**: Discuss irrigation, pest control, organic farming, etc.

### 📊 Supported Crops

Current database includes:
- **Apple** (Malus domestica)
  - Apple Scab
  - Fire Blight
- **Tomato** (Solanum lycopersicum)
  - Early Blight
  - Late Blight
- **Corn** (Zea mays)
  - Corn Smut
  - Northern Leaf Blight

## 🧪 Development

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black app/
flake8 app/
```

### Database Migration
```bash
python scripts/setup_database.py
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Flask Configuration
FLASK_DEBUG=True
FLASK_HOST=127.0.0.1
FLASK_PORT=5000

# Database
DATABASE_URL=sqlite:///crop_disease.db

# Security
SECRET_KEY=your-secret-key-here

# File Upload
MAX_CONTENT_LENGTH=16777216
UPLOAD_FOLDER=static/uploads
```

### Production Deployment

For production deployment:

1. Set `FLASK_ENV=production` in `.env`
2. Use PostgreSQL instead of SQLite
3. Configure proper SSL certificates
4. Set up reverse proxy (Nginx)
5. Enable monitoring and logging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📋 API Documentation

### Upload Endpoint
```http
POST /upload
Content-Type: multipart/form-data

Response:
{
  "success": true,
  "result_id": "uuid",
  "analysis": {...},
  "image_url": "/static/uploads/filename.jpg"
}
```

### Chat Endpoint
```http
POST /chat
Content-Type: application/json

{
  "message": "What causes tomato blight?",
  "session_id": "uuid"
}

Response:
{
  "response": "Tomato blight is caused by...",
  "session_id": "uuid"
}
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- Your Name - Initial work - [YourGitHub](https://github.com/yourusername)

## 🙏 Acknowledgments

- Agricultural research communities for disease information
- Open source computer vision libraries
- Flask and Python communities
- Farmers and agricultural professionals for feedback

## 📞 Support

For support, email support@cropdetection.com or create an issue on GitHub.

## 🔄 Version History

- **v1.0.0** - Initial release with basic disease detection
- **v1.1.0** - Added chatbot functionality
- **v1.2.0** - Enhanced UI/UX and mobile responsiveness
- **v1.3.0** - Docker containerization and production deployment

---

**Made with ❤️ for farmers and agricultural professionals worldwide** 🌾