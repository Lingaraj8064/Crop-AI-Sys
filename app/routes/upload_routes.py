"""
Crop Disease Detection System - Upload Routes
Routes for handling image upload and disease analysis
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.models.database import AnalysisResult
from app.services.disease_detector import DiseaseDetectionService
from app.services.image_processor import ImageProcessor
from app.utils.file_handler import FileHandler
from app.utils.validators import validate_image_file
from app import db
import os
import uuid
import logging
from datetime import datetime
import time

# Create blueprint
bp = Blueprint('upload', __name__, url_prefix='/upload')

# Initialize services
disease_detector = DiseaseDetectionService()
image_processor = ImageProcessor()
file_handler = FileHandler()

@bp.route('/', methods=['POST'])
def upload_image():
    """
    Handle image upload and disease analysis
    
    Expected: multipart/form-data with 'file' field
    Returns: JSON with analysis results
    """
    start_time = time.time()
    
    try:
        # Validate request
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded',
                'code': 'NO_FILE'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'code': 'EMPTY_FILENAME'
            }), 400
        
        # Validate file
        validation_result = validate_image_file(file)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': validation_result['error'],
                'code': 'INVALID_FILE'
            }), 400
        
        # Get client information
        user_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        # Process and save file
        file_info = file_handler.save_uploaded_file(file)
        if not file_info['success']:
            return jsonify({
                'success': False,
                'error': file_info['error'],
                'code': 'FILE_SAVE_ERROR'
            }), 500
        
        saved_filename = file_info['filename']
        file_path = file_info['file_path']
        
        try:
            # Preprocess image
            processed_image_info = image_processor.preprocess_for_analysis(file_path)
            if not processed_image_info['success']:
                # Clean up file
                file_handler.delete_file(file_path)
                return jsonify({
                    'success': False,
                    'error': processed_image_info['error'],
                    'code': 'IMAGE_PROCESSING_ERROR'
                }), 500
            
            # Perform disease detection
            analysis_result = disease_detector.analyze_image(file_path)
            if not analysis_result['success']:
                # Clean up file
                file_handler.delete_file(file_path)
                return jsonify({
                    'success': False,
                    'error': analysis_result['error'],
                    'code': 'ANALYSIS_ERROR'
                }), 500
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Create database record
            result_id = str(uuid.uuid4())
            db_result = AnalysisResult(
                id=result_id,
                filename=saved_filename,
                original_filename=file.filename,
                file_size=file_info.get('file_size', 0),
                file_type=file_info.get('file_type', ''),
                plant_name=analysis_result['data']['plant_name'],
                scientific_name=analysis_result['data'].get('scientific_name', ''),
                disease_name=analysis_result['data'].get('disease_name'),
                is_healthy=analysis_result['data']['is_healthy'],
                confidence=analysis_result['data']['confidence'],
                severity_level=analysis_result['data'].get('severity'),
                analysis_data=analysis_result['data_json'],
                processing_time=processing_time,
                model_version=analysis_result['data'].get('model_version', '1.0.0'),
                user_ip=user_ip,
                user_agent=user_agent
            )
            
            db.session.add(db_result)
            db.session.commit()
            
            # Prepare response
            response_data = {
                'success': True,
                'result_id': result_id,
                'analysis': analysis_result['data'],
                'image_url': f'/static/uploads/{saved_filename}',
                'processing_time': round(processing_time, 2),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logging.info(f"Successful analysis: {result_id} - {analysis_result['data']['plant_name']}")
            return jsonify(response_data), 200
            
        except Exception as analysis_error:
            # Clean up file on analysis error
            file_handler.delete_file(file_path)
            raise analysis_error
            
    except Exception as e:
        logging.error(f"Upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error occurred during analysis',
            'code': 'INTERNAL_ERROR'
        }), 500

@bp.route('/batch', methods=['POST'])
def batch_upload():
    """
    Handle multiple image uploads for batch processing
    
    Expected: multipart/form-data with multiple 'files' fields
    Returns: JSON with batch analysis results
    """
    start_time = time.time()
    
    try:
        if 'files' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No files uploaded',
                'code': 'NO_FILES'
            }), 400
        
        files = request.files.getlist('files')
        if not files or all(file.filename == '' for file in files):
            return jsonify({
                'success': False,
                'error': 'No files selected',
                'code': 'EMPTY_FILES'
            }), 400
        
        # Limit batch size
        max_batch_size = current_app.config.get('MAX_BATCH_SIZE', 5)
        if len(files) > max_batch_size:
            return jsonify({
                'success': False,
                'error': f'Too many files. Maximum {max_batch_size} files allowed',
                'code': 'BATCH_SIZE_EXCEEDED'
            }), 400
        
        results = []
        successful_analyses = 0
        failed_analyses = 0
        
        user_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        user_agent = request.headers.get('User-Agent', '')
        
        for i, file in enumerate(files):
            try:
                if file.filename == '':
                    results.append({
                        'index': i,
                        'success': False,
                        'error': 'Empty filename',
                        'filename': ''
                    })
                    failed_analyses += 1
                    continue
                
                # Validate file
                validation_result = validate_image_file(file)
                if not validation_result['valid']:
                    results.append({
                        'index': i,
                        'success': False,
                        'error': validation_result['error'],
                        'filename': file.filename
                    })
                    failed_analyses += 1
                    continue
                
                # Process single file
                file_info = file_handler.save_uploaded_file(file)
                if not file_info['success']:
                    results.append({
                        'index': i,
                        'success': False,
                        'error': file_info['error'],
                        'filename': file.filename
                    })
                    failed_analyses += 1
                    continue
                
                # Analyze image
                analysis_result = disease_detector.analyze_image(file_info['file_path'])
                if not analysis_result['success']:
                    file_handler.delete_file(file_info['file_path'])
                    results.append({
                        'index': i,
                        'success': False,
                        'error': analysis_result['error'],
                        'filename': file.filename
                    })
                    failed_analyses += 1
                    continue
                
                # Save to database
                result_id = str(uuid.uuid4())
                db_result = AnalysisResult(
                    id=result_id,
                    filename=file_info['filename'],
                    original_filename=file.filename,
                    file_size=file_info.get('file_size', 0),
                    file_type=file_info.get('file_type', ''),
                    plant_name=analysis_result['data']['plant_name'],
                    disease_name=analysis_result['data'].get('disease_name'),
                    is_healthy=analysis_result['data']['is_healthy'],
                    confidence=analysis_result['data']['confidence'],
                    severity_level=analysis_result['data'].get('severity'),
                    analysis_data=analysis_result['data_json'],
                    processing_time=analysis_result['data'].get('processing_time', 0),
                    model_version=analysis_result['data'].get('model_version', '1.0.0'),
                    user_ip=user_ip,
                    user_agent=user_agent
                )
                
                db.session.add(db_result)
                
                results.append({
                    'index': i,
                    'success': True,
                    'result_id': result_id,
                    'filename': file.filename,
                    'analysis': analysis_result['data'],
                    'image_url': f'/static/uploads/{file_info["filename"]}'
                })
                
                successful_analyses += 1
                
            except Exception as file_error:
                logging.error(f"Error processing file {file.filename}: {file_error}")
                results.append({
                    'index': i,
                    'success': False,
                    'error': 'Processing error occurred',
                    'filename': file.filename
                })
                failed_analyses += 1
        
        # Commit all successful analyses
        if successful_analyses > 0:
            db.session.commit()
        
        total_processing_time = time.time() - start_time
        
        response_data = {
            'success': True,
            'batch_summary': {
                'total_files': len(files),
                'successful_analyses': successful_analyses,
                'failed_analyses': failed_analyses,
                'processing_time': round(total_processing_time, 2)
            },
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logging.info(f"Batch upload completed: {successful_analyses}/{len(files)} successful")
        return jsonify(response_data), 200
        
    except Exception as e:
        logging.error(f"Batch upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error during batch processing',
            'code': 'BATCH_ERROR'
        }), 500

@bp.route('/url', methods=['POST'])
def upload_from_url():
    """
    Analyze image from URL
    
    Expected: JSON with 'image_url' field
    Returns: JSON with analysis results
    """
    try:
        data = request.get_json()
        if not data or 'image_url' not in data:
            return jsonify({
                'success': False,
                'error': 'Image URL is required',
                'code': 'NO_URL'
            }), 400
        
        image_url = data['image_url']
        
        # Download and process image from URL
        download_result = file_handler.download_image_from_url(image_url)
        if not download_result['success']:
            return jsonify({
                'success': False,
                'error': download_result['error'],
                'code': 'URL_DOWNLOAD_ERROR'
            }), 400
        
        file_path = download_result['file_path']
        filename = download_result['filename']
        
        try:
            # Analyze the downloaded image
            analysis_result = disease_detector.analyze_image(file_path)
            if not analysis_result['success']:
                file_handler.delete_file(file_path)
                return jsonify({
                    'success': False,
                    'error': analysis_result['error'],
                    'code': 'ANALYSIS_ERROR'
                }), 500
            
            # Save to database
            result_id = str(uuid.uuid4())
            user_ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
            user_agent = request.headers.get('User-Agent', '')
            
            db_result = AnalysisResult(
                id=result_id,
                filename=filename,
                original_filename=f"url_download_{filename}",
                plant_name=analysis_result['data']['plant_name'],
                disease_name=analysis_result['data'].get('disease_name'),
                is_healthy=analysis_result['data']['is_healthy'],
                confidence=analysis_result['data']['confidence'],
                severity_level=analysis_result['data'].get('severity'),
                analysis_data=analysis_result['data_json'],
                processing_time=analysis_result['data'].get('processing_time', 0),
                model_version=analysis_result['data'].get('model_version', '1.0.0'),
                user_ip=user_ip,
                user_agent=user_agent
            )
            
            db.session.add(db_result)
            db.session.commit()
            
            response_data = {
                'success': True,
                'result_id': result_id,
                'analysis': analysis_result['data'],
                'image_url': f'/static/uploads/{filename}',
                'source_url': image_url,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logging.info(f"URL analysis completed: {result_id}")
            return jsonify(response_data), 200
            
        except Exception as analysis_error:
            file_handler.delete_file(file_path)
            raise analysis_error
            
    except Exception as e:
        logging.error(f"URL upload error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error processing image from URL',
            'code': 'URL_ERROR'
        }), 500

@bp.route('/status/<result_id>')
def get_upload_status(result_id):
    """Get analysis status by result ID"""
    try:
        result = AnalysisResult.query.get(result_id)
        if not result:
            return jsonify({
                'success': False,
                'error': 'Result not found',
                'code': 'NOT_FOUND'
            }), 404
        
        return jsonify({
            'success': True,
            'result': result.to_dict()
        }), 200
        
    except Exception as e:
        logging.error(f"Error getting upload status: {e}")
        return jsonify({
            'success': False,
            'error': 'Error retrieving status',
            'code': 'STATUS_ERROR'
        }), 500