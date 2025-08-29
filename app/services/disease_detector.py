"""
Crop Disease Detection System - Disease Detection Service
Main service for AI-powered plant disease detection
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
from PIL import Image

from app.models.ml_model import CropDiseaseModel
from app.models.plant_database import PlantDatabase
from app.services.image_processor import ImageProcessor

class DiseaseDetectionService:
    """Service class for plant disease detection using AI models"""
    
    def __init__(self):
        """Initialize the disease detection service"""
        self.model = CropDiseaseModel()
        self.plant_db = PlantDatabase()
        self.image_processor = ImageProcessor()
        self.confidence_threshold = 0.7
        self.is_initialized = False
        
        # Initialize service
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize the service components"""
        try:
            # Check if model is ready
            if self.model.health_check():
                self.is_initialized = True
                logging.info("Disease detection service initialized successfully")
            else:
                logging.warning("Disease detection service initialized with mock model")
                self.is_initialized = True  # Still functional with mock
                
        except Exception as e:
            logging.error(f"Error initializing disease detection service: {e}")
            self.is_initialized = False
    
    def analyze_image(self, image_path: str, options: Dict = None) -> Dict:
        """
        Analyze an image for plant disease detection
        
        Args:
            image_path: Path to the image file
            options: Optional analysis parameters
            
        Returns:
            Dictionary containing analysis results
        """
        start_time = time.time()
        
        if not self.is_initialized:
            return {
                'success': False,
                'error': 'Service not properly initialized',
                'code': 'SERVICE_NOT_READY'
            }
        
        try:
            # Validate image file
            if not os.path.exists(image_path):
                return {
                    'success': False,
                    'error': 'Image file not found',
                    'code': 'FILE_NOT_FOUND'
                }
            
            # Preprocess image if needed
            preprocessing_result = self.image_processor.preprocess_for_analysis(image_path)
            if not preprocessing_result['success']:
                return {
                    'success': False,
                    'error': preprocessing_result['error'],
                    'code': 'PREPROCESSING_ERROR'
                }
            
            # Get AI model prediction
            prediction_result = self.model.predict(image_path)
            if 'error' in prediction_result:
                return {
                    'success': False,
                    'error': prediction_result['error'],
                    'code': 'PREDICTION_ERROR'
                }
            
            # Process and enhance results
            enhanced_result = self._enhance_prediction_results(prediction_result)
            
            # Add metadata
            enhanced_result.update({
                'processing_time': time.time() - start_time,
                'image_path': image_path,
                'analysis_timestamp': time.time(),
                'service_version': '1.0.0'
            })
            
            # Create final response
            analysis_data = {
                'plant_name': enhanced_result['plant_name'],
                'scientific_name': enhanced_result.get('scientific_name', ''),
                'is_healthy': enhanced_result['is_healthy'],
                'confidence': enhanced_result['confidence'],
                'severity': enhanced_result.get('severity'),
                'disease_name': enhanced_result.get('disease_name'),
                'symptoms': enhanced_result.get('symptoms', ''),
                'causes': enhanced_result.get('causes', ''),
                'treatment': enhanced_result.get('treatment', []),
                'prevention': enhanced_result.get('prevention', []),
                'immediate_action': enhanced_result.get('immediate_action', ''),
                'soil_conditions': enhanced_result.get('soil_conditions', {}),
                'weather_conditions': enhanced_result.get('weather_conditions', {}),
                'suitable_regions': enhanced_result.get('suitable_regions', []),
                'care_instructions': enhanced_result.get('care_instructions', {}),
                'model_version': enhanced_result.get('model_version', '1.0.0'),
                'processing_time': enhanced_result['processing_time']
            }
            
            return {
                'success': True,
                'data': analysis_data,
                'data_json': json.dumps(analysis_data),
                'confidence_level': self._get_confidence_level(enhanced_result['confidence']),
                'recommendations': self._generate_recommendations(enhanced_result)
            }
            
        except Exception as e:
            logging.error(f"Error in disease analysis: {e}")
            return {
                'success': False,
                'error': 'Analysis failed due to internal error',
                'code': 'ANALYSIS_FAILED',
                'processing_time': time.time() - start_time
            }
    
    def _enhance_prediction_results(self, prediction_result: Dict) -> Dict:
        """Enhance AI prediction results with detailed plant information"""
        try:
            enhanced = prediction_result.copy()
            
            # Get plant information from database
            plant_name = prediction_result['plant_name']
            plant_info = self.plant_db.get_plant_by_name(plant_name)
            
            if plant_info:
                enhanced['scientific_name'] = plant_info.scientific_name
                enhanced['soil_conditions'] = plant_info.soil_requirements.to_dict()
                enhanced['weather_conditions'] = plant_info.weather_requirements.to_dict()
                enhanced['suitable_regions'] = plant_info.suitable_regions
                enhanced['care_instructions'] = plant_info.care_instructions.to_dict()
                
                # If diseased, get disease information
                if not prediction_result['is_healthy'] and prediction_result.get('disease_name'):
                    disease_info = plant_info.get_disease_by_name(prediction_result['disease_name'])
                    if disease_info:
                        enhanced.update({
                            'symptoms': disease_info.symptoms,
                            'causes': disease_info.causes,
                            'treatment': disease_info.treatment,
                            'prevention': disease_info.prevention,
                            'immediate_action': disease_info.immediate_action,
                            'organic_treatment': disease_info.organic_treatment,
                            'affected_parts': disease_info.affected_parts,
                            'favorable_conditions': disease_info.favorable_conditions,
                            'spread_method': disease_info.spread_method,
                            'contagious_level': disease_info.contagious_level
                        })
                
                # If healthy, get care information
                elif prediction_result['is_healthy']:
                    enhanced['care_tips'] = plant_info.care_instructions.to_dict()
                    enhanced['growth_optimization'] = self._get_growth_optimization_tips(plant_info)
            
            return enhanced
            
        except Exception as e:
            logging.error(f"Error enhancing prediction results: {e}")
            return prediction_result
    
    def _get_growth_optimization_tips(self, plant_info) -> List[str]:
        """Generate growth optimization tips for healthy plants"""
        tips = []
        
        # Soil optimization
        soil_req = plant_info.soil_requirements
        tips.append(f"Maintain soil pH between {soil_req.ph_min}-{soil_req.ph_max} for optimal growth")
        tips.append(f"Ensure {soil_req.drainage.lower()} for proper root health")
        
        # Weather optimization
        weather_req = plant_info.weather_requirements
        tips.append(f"Provide {weather_req.sunlight_hours} for maximum photosynthesis")
        
        # Care optimization
        care = plant_info.care_instructions
        if care.watering:
            tips.extend(care.watering[:2])  # Top 2 watering tips
        
        return tips[:5]  # Return top 5 tips
    
    def _get_confidence_level(self, confidence: float) -> str:
        """Convert confidence percentage to descriptive level"""
        if confidence >= 95:
            return "Very High"
        elif confidence >= 85:
            return "High"
        elif confidence >= 75:
            return "Medium"
        elif confidence >= 60:
            return "Low"
        else:
            return "Very Low"
    
    def _generate_recommendations(self, analysis_result: Dict) -> List[Dict]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        try:
            confidence = analysis_result.get('confidence', 0)
            is_healthy = analysis_result.get('is_healthy', True)
            severity = analysis_result.get('severity', '')
            
            # Confidence-based recommendations
            if confidence < 80:
                recommendations.append({
                    'type': 'image_quality',
                    'priority': 'medium',
                    'title': 'Consider Retaking Photo',
                    'description': 'For better accuracy, try taking a clearer photo with better lighting and focus on affected areas.'
                })
            
            # Disease-specific recommendations
            if not is_healthy:
                if severity == 'Critical':
                    recommendations.append({
                        'type': 'urgent_action',
                        'priority': 'high',
                        'title': 'Immediate Action Required',
                        'description': analysis_result.get('immediate_action', 'Take immediate steps to prevent disease spread.')
                    })
                
                # Treatment recommendations
                treatments = analysis_result.get('treatment', [])
                if treatments:
                    recommendations.append({
                        'type': 'treatment',
                        'priority': 'high',
                        'title': 'Treatment Plan',
                        'description': f"Follow these steps: {', '.join(treatments[:3])}"
                    })
                
                # Prevention for future
                prevention = analysis_result.get('prevention', [])
                if prevention:
                    recommendations.append({
                        'type': 'prevention',
                        'priority': 'medium',
                        'title': 'Prevention Tips',
                        'description': f"Prevent recurrence: {', '.join(prevention[:2])}"
                    })
            
            # Healthy plant recommendations
            else:
                care_tips = analysis_result.get('care_instructions', {}).get('watering', [])
                if care_tips:
                    recommendations.append({
                        'type': 'maintenance',
                        'priority': 'low',
                        'title': 'Continued Care',
                        'description': f"Maintain plant health: {care_tips[0] if care_tips else 'Continue regular care routine'}"
                    })
            
            # General growing condition recommendations
            soil_conditions = analysis_result.get('soil_conditions', {})
            if soil_conditions:
                recommendations.append({
                    'type': 'growing_conditions',
                    'priority': 'medium',
                    'title': 'Optimal Growing Conditions',
                    'description': f"Soil pH: {soil_conditions.get('ph_range', 'N/A')}, {soil_conditions.get('drainage', 'Well-draining soil preferred')}"
                })
            
        except Exception as e:
            logging.error(f"Error generating recommendations: {e}")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def batch_analyze(self, image_paths: List[str], options: Dict = None) -> List[Dict]:
        """
        Analyze multiple images in batch
        
        Args:
            image_paths: List of image file paths
            options: Optional analysis parameters
            
        Returns:
            List of analysis results
        """
        results = []
        
        for i, image_path in enumerate(image_paths):
            try:
                result = self.analyze_image(image_path, options)
                result['batch_index'] = i
                result['image_path'] = image_path
                results.append(result)
                
            except Exception as e:
                logging.error(f"Error in batch analysis for image {i}: {e}")
                results.append({
                    'success': False,
                    'batch_index': i,
                    'image_path': image_path,
                    'error': f'Analysis failed: {str(e)}',
                    'code': 'BATCH_ITEM_FAILED'
                })
        
        return results
    
    def validate_image_for_analysis(self, image_path: str) -> Dict:
        """
        Validate if image is suitable for disease analysis
        
        Args:
            image_path: Path to image file
            
        Returns:
            Validation result dictionary
        """
        try:
            if not os.path.exists(image_path):
                return {
                    'valid': False,
                    'error': 'Image file not found',
                    'code': 'FILE_NOT_FOUND'
                }
            
            # Check file size
            file_size = os.path.getsize(image_path)
            if file_size > 16 * 1024 * 1024:  # 16MB limit
                return {
                    'valid': False,
                    'error': 'Image file too large (max 16MB)',
                    'code': 'FILE_TOO_LARGE'
                }
            
            # Validate image format
            validation_result = self.image_processor.validate_image(image_path)
            if not validation_result['valid']:
                return validation_result
            
            # Check image quality
            quality_result = self.image_processor.assess_image_quality(image_path)
            
            return {
                'valid': True,
                'file_size': file_size,
                'quality_assessment': quality_result,
                'recommendations': self._get_image_quality_recommendations(quality_result)
            }
            
        except Exception as e:
            logging.error(f"Error validating image: {e}")
            return {
                'valid': False,
                'error': 'Error validating image file',
                'code': 'VALIDATION_ERROR'
            }
    
    def _get_image_quality_recommendations(self, quality_result: Dict) -> List[str]:
        """Generate recommendations for improving image quality"""
        recommendations = []
        
        if quality_result.get('blur_score', 0) < 0.5:
            recommendations.append("Image appears blurry - try holding camera steady")
        
        if quality_result.get('brightness_score', 0.5) < 0.3:
            recommendations.append("Image is too dark - try better lighting")
        elif quality_result.get('brightness_score', 0.5) > 0.8:
            recommendations.append("Image is too bright - reduce direct light")
        
        if quality_result.get('plant_coverage', 0) < 0.4:
            recommendations.append("Get closer to the plant for better coverage")
        
        return recommendations
    
    def get_service_info(self) -> Dict:
        """Get information about the service and its capabilities"""
        return {
            'service_name': 'Disease Detection Service',
            'version': '1.0.0',
            'is_initialized': self.is_initialized,
            'model_info': self.model.get_model_info(),
            'supported_plants': [plant.common_name for plant in self.plant_db.get_all_plants()],
            'supported_diseases': [disease.name for disease in self.plant_db.get_all_diseases()],
            'confidence_threshold': self.confidence_threshold,
            'capabilities': [
                'Plant species identification',
                'Disease detection and classification',
                'Treatment recommendations',
                'Prevention strategies',
                'Care instructions',
                'Batch processing',
                'Image quality assessment'
            ]
        }
    
    def health_check(self) -> Dict:
        """Perform service health check"""
        try:
            # Check model health
            model_healthy = self.model.health_check()
            
            # Check plant database
            plant_count = len(self.plant_db.get_all_plants())
            disease_count = len(self.plant_db.get_all_diseases())
            
            # Check image processor
            processor_healthy = self.image_processor.health_check()
            
            is_healthy = (
                self.is_initialized and 
                model_healthy and 
                processor_healthy and 
                plant_count > 0 and 
                disease_count > 0
            )
            
            return {
                'healthy': is_healthy,
                'service_initialized': self.is_initialized,
                'model_ready': model_healthy,
                'image_processor_ready': processor_healthy,
                'plant_database': {
                    'plants_loaded': plant_count,
                    'diseases_loaded': disease_count
                },
                'timestamp': time.time()
            }
            
        except Exception as e:
            logging.error(f"Health check failed: {e}")
            return {
                'healthy': False,
                'error': str(e),
                'timestamp': time.time()
            }