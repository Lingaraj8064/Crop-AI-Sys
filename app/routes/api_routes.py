"""
Crop Disease Detection System - API Routes
RESTful API endpoints for external integrations
"""

from flask import Blueprint, jsonify, request, current_app
from app.models.database import AnalysisResult, ChatSession, SystemLog
from app.models.plant_database import PlantDatabase
from app import db
import logging
from datetime import datetime, timedelta
from sqlalchemy import func, desc

# Create blueprint
bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Initialize plant database
plant_db = PlantDatabase()

# API versioning and documentation
@bp.route('/')
def api_info():
    """API information and available endpoints"""
    return jsonify({
        'name': 'Crop Disease Detection API',
        'version': '1.0.0',
        'description': 'RESTful API for crop disease detection and agricultural information',
        'endpoints': {
            'plants': '/api/v1/plants - Get all plants',
            'plant_detail': '/api/v1/plants/<id> - Get plant details',
            'diseases': '/api/v1/diseases - Get all diseases',
            'disease_detail': '/api/v1/diseases/<id> - Get disease details',
            'results': '/api/v1/results - Get analysis results',
            'result_detail': '/api/v1/results/<id> - Get specific result',
            'stats': '/api/v1/stats - Get system statistics',
            'search': '/api/v1/search - Search plants and diseases'
        },
        'authentication': 'None required for current version',
        'rate_limiting': 'Not implemented in current version',
        'documentation': '/api/v1/docs'
    })

# Plant-related endpoints
@bp.route('/plants')
def get_plants():
    """Get all plants with optional filtering"""
    try:
        # Get query parameters
        category = request.args.get('category', '')
        search = request.args.get('search', '')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Validate limit
        if limit > 100:
            limit = 100
        
        plants = plant_db.get_all_plants()
        
        # Apply filters
        if category:
            plants = [plant for plant in plants 
                     if plant.category.value.lower() == category.lower()]
        
        if search:
            search_lower = search.lower()
            plants = [plant for plant in plants 
                     if (search_lower in plant.common_name.lower() or 
                         search_lower in plant.scientific_name.lower() or
                         search_lower in plant.family.lower())]
        
        # Apply pagination
        total_plants = len(plants)
        plants = plants[offset:offset + limit]
        
        # Convert to dict format
        plants_data = []
        for plant in plants:
            plant_dict = plant.to_dict()
            # Remove detailed information for list view
            plant_dict.pop('care_instructions', None)
            plant_dict.pop('diseases', None)
            plants_data.append(plant_dict)
        
        return jsonify({
            'success': True,
            'data': plants_data,
            'pagination': {
                'total': total_plants,
                'offset': offset,
                'limit': limit,
                'count': len(plants_data)
            },
            'filters': {
                'category': category,
                'search': search
            }
        })
        
    except Exception as e:
        logging.error(f"API error getting plants: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve plants',
            'message': str(e)
        }), 500

@bp.route('/plants/<plant_id>')
def get_plant_detail(plant_id):
    """Get detailed plant information"""
    try:
        plant = plant_db.get_plant(plant_id)
        if not plant:
            return jsonify({
                'success': False,
                'error': 'Plant not found',
                'plant_id': plant_id
            }), 404
        
        # Get analysis statistics for this plant
        total_analyses = AnalysisResult.query.filter(
            AnalysisResult.plant_name == plant.common_name
        ).count()
        
        healthy_count = AnalysisResult.query.filter(
            AnalysisResult.plant_name == plant.common_name,
            AnalysisResult.is_healthy == True
        ).count()
        
        # Get recent analyses
        recent_analyses = AnalysisResult.query.filter(
            AnalysisResult.plant_name == plant.common_name
        ).order_by(desc(AnalysisResult.created_at)).limit(5).all()
        
        plant_data = plant.to_dict()
        plant_data['statistics'] = {
            'total_analyses': total_analyses,
            'healthy_count': healthy_count,
            'diseased_count': total_analyses - healthy_count,
            'health_percentage': round((healthy_count / total_analyses * 100), 1) if total_analyses > 0 else 0,
            'recent_analyses': [result.to_dict() for result in recent_analyses]
        }
        
        return jsonify({
            'success': True,
            'data': plant_data
        })
        
    except Exception as e:
        logging.error(f"API error getting plant detail {plant_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve plant details',
            'message': str(e)
        }), 500

# Disease-related endpoints
@bp.route('/diseases')
def get_diseases():
    """Get all diseases with optional filtering"""
    try:
        severity = request.args.get('severity', '')
        search = request.args.get('search', '')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        if limit > 100:
            limit = 100
        
        diseases = plant_db.get_all_diseases()
        
        # Apply filters
        if severity:
            diseases = [disease for disease in diseases 
                       if disease.severity.value.lower() == severity.lower()]
        
        if search:
            search_lower = search.lower()
            diseases = [disease for disease in diseases 
                       if search_lower in disease.name.lower()]
        
        # Apply pagination
        total_diseases = len(diseases)
        diseases = diseases[offset:offset + limit]
        
        # Convert to dict format
        diseases_data = [disease.to_dict() for disease in diseases]
        
        return jsonify({
            'success': True,
            'data': diseases_data,
            'pagination': {
                'total': total_diseases,
                'offset': offset,
                'limit': limit,
                'count': len(diseases_data)
            },
            'filters': {
                'severity': severity,
                'search': search
            }
        })
        
    except Exception as e:
        logging.error(f"API error getting diseases: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve diseases',
            'message': str(e)
        }), 500

@bp.route('/diseases/<disease_id>')
def get_disease_detail(disease_id):
    """Get detailed disease information"""
    try:
        disease = plant_db.get_disease(disease_id)
        if not disease:
            return jsonify({
                'success': False,
                'error': 'Disease not found',
                'disease_id': disease_id
            }), 404
        
        # Get analysis statistics for this disease
        total_detections = AnalysisResult.query.filter(
            AnalysisResult.disease_name == disease.name
        ).count()
        
        # Get affected plant types
        affected_plants = db.session.query(
            AnalysisResult.plant_name,
            func.count(AnalysisResult.plant_name).label('count')
        ).filter(
            AnalysisResult.disease_name == disease.name
        ).group_by(AnalysisResult.plant_name).all()
        
        disease_data = disease.to_dict()
        disease_data['statistics'] = {
            'total_detections': total_detections,
            'affected_plant_types': [
                {'plant': plant, 'detections': count}
                for plant, count in affected_plants
            ]
        }
        
        return jsonify({
            'success': True,
            'data': disease_data
        })
        
    except Exception as e:
        logging.error(f"API error getting disease detail {disease_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve disease details',
            'message': str(e)
        }), 500

# Analysis results endpoints
@bp.route('/results')
def get_results():
    """Get analysis results with filtering and pagination"""
    try:
        # Query parameters
        plant_name = request.args.get('plant', '')
        is_healthy = request.args.get('healthy', '', type=str)
        min_confidence = request.args.get('min_confidence', 0, type=float)
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        sort_by = request.args.get('sort', 'created_at')
        sort_order = request.args.get('order', 'desc')
        
        if limit > 100:
            limit = 100
        
        # Build query
        query = AnalysisResult.query
        
        if plant_name:
            query = query.filter(AnalysisResult.plant_name.ilike(f'%{plant_name}%'))
        
        if is_healthy.lower() in ['true', 'false']:
            query = query.filter(AnalysisResult.is_healthy == (is_healthy.lower() == 'true'))
        
        if min_confidence > 0:
            query = query.filter(AnalysisResult.confidence >= min_confidence)
        
        # Apply sorting
        if sort_by == 'confidence':
            order_column = AnalysisResult.confidence
        elif sort_by == 'plant_name':
            order_column = AnalysisResult.plant_name
        else:
            order_column = AnalysisResult.created_at
        
        if sort_order.lower() == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())
        
        # Get total count
        total_results = query.count()
        
        # Apply pagination
        results = query.offset(offset).limit(limit).all()
        
        # Convert to dict format
        results_data = [result.to_dict() for result in results]
        
        return jsonify({
            'success': True,
            'data': results_data,
            'pagination': {
                'total': total_results,
                'offset': offset,
                'limit': limit,
                'count': len(results_data)
            },
            'filters': {
                'plant': plant_name,
                'healthy': is_healthy,
                'min_confidence': min_confidence,
                'sort_by': sort_by,
                'sort_order': sort_order
            }
        })
        
    except Exception as e:
        logging.error(f"API error getting results: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve results',
            'message': str(e)
        }), 500

@bp.route('/results/<result_id>')
def get_result_detail(result_id):
    """Get detailed analysis result"""
    try:
        result = AnalysisResult.query.get(result_id)
        if not result:
            return jsonify({
                'success': False,
                'error': 'Result not found',
                'result_id': result_id
            }), 404
        
        result_data = result.to_dict()
        
        # Add plant information if available
        plant = plant_db.get_plant_by_name(result.plant_name)
        if plant:
            result_data['plant_info'] = plant.to_dict()
            
            # Add disease information if diseased
            if result.disease_name and not result.is_healthy:
                disease = plant.get_disease_by_name(result.disease_name)
                if disease:
                    result_data['disease_info'] = disease.to_dict()
        
        return jsonify({
            'success': True,
            'data': result_data
        })
        
    except Exception as e:
        logging.error(f"API error getting result detail {result_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve result details',
            'message': str(e)
        }), 500

# Statistics endpoints
@bp.route('/stats')
def get_system_stats():
    """Get comprehensive system statistics"""
    try:
        # Time-based queries
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Basic counts
        total_analyses = AnalysisResult.query.count()
        healthy_count = AnalysisResult.query.filter(AnalysisResult.is_healthy == True).count()
        diseased_count = total_analyses - healthy_count
        
        # Recent activity
        recent_analyses = AnalysisResult.query.filter(
            AnalysisResult.created_at >= week_ago
        ).count()
        
        monthly_analyses = AnalysisResult.query.filter(
            AnalysisResult.created_at >= month_ago
        ).count()
        
        # Top diseases
        top_diseases = db.session.query(
            AnalysisResult.disease_name,
            func.count(AnalysisResult.disease_name).label('count')
        ).filter(
            AnalysisResult.disease_name.isnot(None)
        ).group_by(AnalysisResult.disease_name).order_by(
            func.count(AnalysisResult.disease_name).desc()
        ).limit(10).all()
        
        # Top plants analyzed
        top_plants = db.session.query(
            AnalysisResult.plant_name,
            func.count(AnalysisResult.plant_name).label('count')
        ).group_by(AnalysisResult.plant_name).order_by(
            func.count(AnalysisResult.plant_name).desc()
        ).limit(10).all()
        
        # Average confidence scores
        avg_confidence = db.session.query(
            func.avg(AnalysisResult.confidence)
        ).scalar() or 0
        
        # Confidence distribution
        confidence_ranges = {
            'high': AnalysisResult.query.filter(AnalysisResult.confidence >= 90).count(),
            'medium': AnalysisResult.query.filter(
                AnalysisResult.confidence >= 70,
                AnalysisResult.confidence < 90
            ).count(),
            'low': AnalysisResult.query.filter(AnalysisResult.confidence < 70).count()
        }
        
        # Chat statistics
        total_chats = ChatSession.query.count()
        recent_chats = ChatSession.query.filter(
            ChatSession.created_at >= week_ago
        ).count()
        
        stats = {
            'overview': {
                'total_analyses': total_analyses,
                'healthy_count': healthy_count,
                'diseased_count': diseased_count,
                'health_percentage': round((healthy_count / total_analyses * 100), 1) if total_analyses > 0 else 0,
                'average_confidence': round(avg_confidence, 1)
            },
            'activity': {
                'recent_analyses_7d': recent_analyses,
                'monthly_analyses_30d': monthly_analyses,
                'total_chat_sessions': total_chats,
                'recent_chats_7d': recent_chats
            },
            'top_diseases': [
                {'name': disease, 'count': count}
                for disease, count in top_diseases
            ],
            'top_plants': [
                {'name': plant, 'count': count}
                for plant, count in top_plants
            ],
            'confidence_distribution': confidence_ranges,
            'database_info': {
                'plants_available': len(plant_db.get_all_plants()),
                'diseases_available': len(plant_db.get_all_diseases())
            },
            'timestamp': now.isoformat()
        }
        
        return jsonify({
            'success': True,
            'data': stats
        })
        
    except Exception as e:
        logging.error(f"API error getting stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve statistics',
            'message': str(e)
        }), 500

# Search endpoints
@bp.route('/search')
def search():
    """Search across plants, diseases, and analysis results"""
    try:
        query = request.args.get('q', '').strip()
        search_type = request.args.get('type', 'all')  # all, plants, diseases, results
        limit = request.args.get('limit', 20, type=int)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required',
                'message': 'Please provide a search query using the "q" parameter'
            }), 400
        
        if limit > 50:
            limit = 50
        
        results = {
            'query': query,
            'search_type': search_type,
            'results': {}
        }
        
        query_lower = query.lower()
        
        # Search plants
        if search_type in ['all', 'plants']:
            plant_matches = []
            for plant in plant_db.get_all_plants():
                if (query_lower in plant.common_name.lower() or 
                    query_lower in plant.scientific_name.lower() or
                    query_lower in plant.family.lower()):
                    plant_dict = plant.to_dict()
                    # Remove detailed info for search results
                    plant_dict.pop('care_instructions', None)
                    plant_dict.pop('diseases', None)
                    plant_matches.append(plant_dict)
            
            results['results']['plants'] = plant_matches[:limit]
        
        # Search diseases
        if search_type in ['all', 'diseases']:
            disease_matches = []
            for disease in plant_db.get_all_diseases():
                if (query_lower in disease.name.lower() or 
                    (disease.scientific_name and query_lower in disease.scientific_name.lower()) or
                    query_lower in disease.symptoms.lower()):
                    disease_matches.append(disease.to_dict())
            
            results['results']['diseases'] = disease_matches[:limit]
        
        # Search analysis results
        if search_type in ['all', 'results']:
            result_matches = AnalysisResult.query.filter(
                db.or_(
                    AnalysisResult.plant_name.ilike(f'%{query}%'),
                    AnalysisResult.disease_name.ilike(f'%{query}%'),
                    AnalysisResult.original_filename.ilike(f'%{query}%')
                )
            ).order_by(desc(AnalysisResult.created_at)).limit(limit).all()
            
            results['results']['analysis_results'] = [
                result.to_dict() for result in result_matches
            ]
        
        # Count total results
        total_results = sum(
            len(category_results) if isinstance(category_results, list) else 0
            for category_results in results['results'].values()
        )
        
        results['total_results'] = total_results
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        logging.error(f"API error in search: {e}")
        return jsonify({
            'success': False,
            'error': 'Search failed',
            'message': str(e)
        }), 500

# Utility endpoints
@bp.route('/categories')
def get_categories():
    """Get available plant categories"""
    try:
        plants = plant_db.get_all_plants()
        categories = list(set(plant.category.value for plant in plants))
        categories.sort()
        
        return jsonify({
            'success': True,
            'data': {
                'categories': categories,
                'count': len(categories)
            }
        })
        
    except Exception as e:
        logging.error(f"API error getting categories: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve categories',
            'message': str(e)
        }), 500

@bp.route('/severity-levels')
def get_severity_levels():
    """Get available disease severity levels"""
    try:
        diseases = plant_db.get_all_diseases()
        severity_levels = list(set(disease.severity.value for disease in diseases))
        severity_levels.sort(key=lambda x: ['Low', 'Medium', 'High', 'Critical'].index(x))
        
        # Get counts for each severity level
        severity_counts = {}
        for disease in diseases:
            severity = disease.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return jsonify({
            'success': True,
            'data': {
                'severity_levels': [
                    {
                        'name': level,
                        'disease_count': severity_counts.get(level, 0)
                    }
                    for level in severity_levels
                ],
                'total_severities': len(severity_levels)
            }
        })
        
    except Exception as e:
        logging.error(f"API error getting severity levels: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve severity levels',
            'message': str(e)
        }), 500

# Health check endpoint
@bp.route('/health')
def api_health():
    """API health check"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        
        # Check plant database
        plant_count = len(plant_db.get_all_plants())
        disease_count = len(plant_db.get_all_diseases())
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0',
            'database': {
                'status': 'connected',
                'plants_loaded': plant_count,
                'diseases_loaded': disease_count
            },
            'services': {
                'disease_detection': 'available',
                'image_processing': 'available',
                'chatbot': 'available'
            }
        })
        
    except Exception as e:
        logging.error(f"API health check failed: {e}")
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

# Error handlers
@bp.errorhandler(404)
def api_not_found(error):
    """API 404 handler"""
    return jsonify({
        'success': False,
        'error': 'API endpoint not found',
        'message': 'The requested API endpoint does not exist',
        'available_endpoints': '/api/v1/ for list of endpoints'
    }), 404

@bp.errorhandler(405)
def method_not_allowed(error):
    """API method not allowed handler"""
    return jsonify({
        'success': False,
        'error': 'Method not allowed',
        'message': 'The HTTP method is not allowed for this endpoint'
    }), 405

@bp.errorhandler(500)
def api_internal_error(error):
    """API 500 handler"""
    return jsonify({
        'success': False,
        'error': 'Internal server error',
        'message': 'An unexpected error occurred while processing the request'
    }), 500