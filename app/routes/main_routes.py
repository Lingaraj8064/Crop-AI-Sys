"""
Crop Disease Detection System - Main Routes
Routes for main pages and navigation
"""

from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from app.models.database import AnalysisResult, SystemLog
from app.models.plant_database import PlantDatabase
from app import db
import logging
from datetime import datetime, timedelta

# Create blueprint
bp = Blueprint('main', __name__)

# Initialize plant database
plant_db = PlantDatabase()

@bp.route('/')
def index():
    """Main dashboard page"""
    try:
        # Get recent analysis statistics
        recent_analyses = AnalysisResult.query.filter(
            AnalysisResult.created_at >= datetime.utcnow() - timedelta(days=7)
        ).count()
        
        # Get top diseases detected
        top_diseases = db.session.query(
            AnalysisResult.disease_name,
            db.func.count(AnalysisResult.disease_name).label('count')
        ).filter(
            AnalysisResult.disease_name.isnot(None)
        ).group_by(AnalysisResult.disease_name).order_by(
            db.func.count(AnalysisResult.disease_name).desc()
        ).limit(5).all()
        
        # Get healthy vs diseased ratio
        total_analyses = AnalysisResult.query.count()
        healthy_count = AnalysisResult.query.filter(AnalysisResult.is_healthy == True).count()
        diseased_count = total_analyses - healthy_count
        
        stats = {
            'recent_analyses': recent_analyses,
            'total_analyses': total_analyses,
            'healthy_count': healthy_count,
            'diseased_count': diseased_count,
            'top_diseases': [{'name': disease, 'count': count} for disease, count in top_diseases],
            'health_percentage': round((healthy_count / total_analyses * 100), 1) if total_analyses > 0 else 0
        }
        
        return render_template('index.html', stats=stats)
        
    except Exception as e:
        logging.error(f"Error loading dashboard: {e}")
        return render_template('index.html', stats={
            'recent_analyses': 0,
            'total_analyses': 0,
            'healthy_count': 0,
            'diseased_count': 0,
            'top_diseases': [],
            'health_percentage': 0
        })

@bp.route('/about')
def about():
    """About page with system information"""
    system_info = {
        'version': '1.0.0',
        'supported_plants': len(plant_db.get_all_plants()),
        'supported_diseases': len(plant_db.get_all_diseases()),
        'features': [
            'AI-powered disease detection',
            'Comprehensive plant database', 
            'Treatment recommendations',
            'Agricultural chatbot assistant',
            'Mobile-responsive design',
            'Real-time image analysis'
        ],
        'technologies': [
            'Python Flask',
            'TensorFlow/Keras',
            'OpenCV',
            'SQLAlchemy',
            'HTML5/CSS3/JavaScript'
        ]
    }
    
    return render_template('about.html', system_info=system_info)

@bp.route('/results/<result_id>')
def view_results(result_id):
    """View detailed analysis results"""
    try:
        result = AnalysisResult.query.get_or_404(result_id)
        
        # Parse analysis data
        import json
        analysis_data = json.loads(result.analysis_data) if result.analysis_data else {}
        
        # Get plant information from database
        plant_info = None
        disease_info = None
        
        if result.plant_name:
            plant_info = plant_db.get_plant_by_name(result.plant_name)
            
            if result.disease_name and plant_info:
                disease_info = plant_info.get_disease_by_name(result.disease_name)
        
        return render_template('results.html', 
                             result=result,
                             analysis_data=analysis_data,
                             plant_info=plant_info,
                             disease_info=disease_info)
                             
    except Exception as e:
        logging.error(f"Error loading results {result_id}: {e}")
        flash('Results not found or error occurred', 'error')
        return redirect(url_for('main.index'))

@bp.route('/history')
def analysis_history():
    """View analysis history"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20
        
        # Get paginated results
        results = AnalysisResult.query.order_by(
            AnalysisResult.created_at.desc()
        ).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return render_template('history.html', results=results)
        
    except Exception as e:
        logging.error(f"Error loading history: {e}")
        flash('Error loading analysis history', 'error')
        return redirect(url_for('main.index'))

@bp.route('/plants')
def plant_library():
    """Plant library and information"""
    try:
        category_filter = request.args.get('category', '')
        search_query = request.args.get('q', '')
        
        plants = plant_db.get_all_plants()
        
        # Apply filters
        if category_filter:
            plants = [plant for plant in plants if plant.category.value.lower() == category_filter.lower()]
        
        if search_query:
            plants = [plant for plant in plants 
                     if search_query.lower() in plant.common_name.lower() 
                     or search_query.lower() in plant.scientific_name.lower()]
        
        # Get available categories
        all_plants = plant_db.get_all_plants()
        categories = list(set(plant.category.value for plant in all_plants))
        categories.sort()
        
        return render_template('plants.html', 
                             plants=plants,
                             categories=categories,
                             selected_category=category_filter,
                             search_query=search_query)
                             
    except Exception as e:
        logging.error(f"Error loading plant library: {e}")
        return render_template('plants.html', 
                             plants=[],
                             categories=[],
                             selected_category='',
                             search_query='')

@bp.route('/plant/<plant_id>')
def plant_detail(plant_id):
    """Detailed plant information page"""
    try:
        plant = plant_db.get_plant(plant_id)
        if not plant:
            flash('Plant not found', 'error')
            return redirect(url_for('main.plant_library'))
        
        # Get recent analyses for this plant
        recent_analyses = AnalysisResult.query.filter(
            AnalysisResult.plant_name == plant.common_name
        ).order_by(AnalysisResult.created_at.desc()).limit(10).all()
        
        # Calculate disease statistics for this plant
        total_analyses = AnalysisResult.query.filter(
            AnalysisResult.plant_name == plant.common_name
        ).count()
        
        healthy_analyses = AnalysisResult.query.filter(
            AnalysisResult.plant_name == plant.common_name,
            AnalysisResult.is_healthy == True
        ).count()
        
        disease_stats = db.session.query(
            AnalysisResult.disease_name,
            db.func.count(AnalysisResult.disease_name).label('count')
        ).filter(
            AnalysisResult.plant_name == plant.common_name,
            AnalysisResult.disease_name.isnot(None)
        ).group_by(AnalysisResult.disease_name).all()
        
        stats = {
            'total_analyses': total_analyses,
            'healthy_count': healthy_analyses,
            'diseased_count': total_analyses - healthy_analyses,
            'disease_distribution': [
                {'name': disease, 'count': count} 
                for disease, count in disease_stats
            ]
        }
        
        return render_template('plant_detail.html', 
                             plant=plant,
                             recent_analyses=recent_analyses,
                             stats=stats)
                             
    except Exception as e:
        logging.error(f"Error loading plant details for {plant_id}: {e}")
        flash('Error loading plant information', 'error')
        return redirect(url_for('main.plant_library'))

@bp.route('/diseases')
def disease_library():
    """Disease library and information"""
    try:
        search_query = request.args.get('q', '')
        severity_filter = request.args.get('severity', '')
        
        diseases = plant_db.get_all_diseases()
        
        # Apply filters
        if severity_filter:
            diseases = [disease for disease in diseases 
                       if disease.severity.value.lower() == severity_filter.lower()]
        
        if search_query:
            diseases = [disease for disease in diseases 
                       if search_query.lower() in disease.name.lower()]
        
        # Get available severity levels
        severity_levels = ['Low', 'Medium', 'High', 'Critical']
        
        return render_template('diseases.html',
                             diseases=diseases,
                             severity_levels=severity_levels,
                             selected_severity=severity_filter,
                             search_query=search_query)
                             
    except Exception as e:
        logging.error(f"Error loading disease library: {e}")
        return render_template('diseases.html',
                             diseases=[],
                             severity_levels=[],
                             selected_severity='',
                             search_query='')

@bp.route('/help')
def help_page():
    """Help and FAQ page"""
    faqs = [
        {
            'question': 'What types of plant diseases can the system detect?',
            'answer': 'Our system can detect common diseases in crops like apple scab, fire blight, early blight, late blight, corn smut, and northern leaf blight. We continuously update our database with new diseases.'
        },
        {
            'question': 'How accurate is the disease detection?',
            'answer': 'Our AI model achieves 85-95% accuracy depending on image quality and disease type. For best results, upload clear, well-lit images of affected plant parts.'
        },
        {
            'question': 'What image formats are supported?',
            'answer': 'We support JPG, PNG, GIF, BMP, TIFF, and WebP formats. Maximum file size is 16MB.'
        },
        {
            'question': 'How should I take photos for best results?',
            'answer': 'Take clear photos in good lighting, focus on affected leaves or plant parts, avoid blurry images, and include symptoms clearly visible.'
        },
        {
            'question': 'Is the service free to use?',
            'answer': 'Yes, our basic disease detection and chatbot services are completely free for all users.'
        }
    ]
    
    return render_template('help.html', faqs=faqs)

@bp.route('/privacy')
def privacy_policy():
    """Privacy policy page"""
    return render_template('privacy.html')

@bp.route('/terms')
def terms_of_service():
    """Terms of service page"""
    return render_template('terms.html')

@bp.route('/health')
def health_check():
    """System health check endpoint"""
    try:
        # Check database connection
        db.session.execute('SELECT 1')
        
        # Check plant database
        plant_count = len(plant_db.get_all_plants())
        disease_count = len(plant_db.get_all_diseases())
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'database_status': 'connected',
            'plant_database': {
                'plants_loaded': plant_count,
                'diseases_loaded': disease_count
            },
            'uptime': 'system_running'
        }
        
        return jsonify(health_data), 200
        
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

# Error handlers
@bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Resource not found'}), 404
    return render_template('errors/404.html'), 404

@bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    db.session.rollback()
    logging.error(f"Internal server error: {error}")
    
    if request.path.startswith('/api/'):
        return jsonify({'error': 'Internal server error'}), 500
    return render_template('errors/500.html'), 500

@bp.errorhandler(413)
def too_large(error):
    """Handle file too large errors"""
    if request.path.startswith('/api/'):
        return jsonify({'error': 'File too large. Maximum size is 16MB'}), 413
    
    flash('File too large. Maximum size is 16MB', 'error')
    return redirect(url_for('main.index'))

# Context processors
@bp.app_context_processor
def inject_global_vars():
    """Inject global variables into templates"""
    return {
        'current_year': datetime.utcnow().year,
        'app_version': '1.0.0',
        'app_name': 'Crop Disease Detection System'
    }