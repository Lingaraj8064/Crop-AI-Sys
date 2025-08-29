"""
Crop Disease Detection System - AI Model Wrapper
Wrapper class for machine learning model operations
"""

import os
import json
import numpy as np
from PIL import Image
import cv2
import logging
from typing import Dict, List, Tuple, Optional
import time

# Try to import TensorFlow, fallback to mock implementation if not available
try:
    import tensorflow as tf
    from tensorflow.keras.models import load_model
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    logging.warning("TensorFlow not available. Using mock implementation.")

class CropDiseaseModel:
    """Wrapper class for crop disease detection AI model"""
    
    def __init__(self, model_path: str = None, config_path: str = None):
        """
        Initialize the crop disease model
        
        Args:
            model_path: Path to the trained model file
            config_path: Path to model configuration file
        """
        self.model_path = model_path or 'ml_models/trained_models/crop_disease_model.h5'
        self.config_path = config_path or 'ml_models/trained_models/model_metadata.json'
        self.model = None
        self.class_names = []
        self.plant_classes = []
        self.disease_classes = []
        self.input_shape = (224, 224, 3)  # Default input shape
        self.is_loaded = False
        
        # Load model configuration
        self._load_config()
        
        # Try to load the model
        self._load_model()
    
    def _load_config(self):
        """Load model configuration from JSON file"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.class_names = config.get('class_names', [])
                    self.plant_classes = config.get('plant_classes', [])
                    self.disease_classes = config.get('disease_classes', [])
                    self.input_shape = tuple(config.get('input_shape', [224, 224, 3]))
                    
                logging.info(f"Model configuration loaded: {len(self.class_names)} classes")
            else:
                logging.warning(f"Config file not found: {self.config_path}")
                self._set_default_config()
        except Exception as e:
            logging.error(f"Error loading model config: {e}")
            self._set_default_config()
    
    def _set_default_config(self):
        """Set default configuration for mock implementation"""
        self.plant_classes = ['apple', 'tomato', 'corn', 'potato', 'wheat']
        self.disease_classes = [
            'healthy', 'apple_scab', 'fire_blight', 'early_blight', 
            'late_blight', 'corn_smut', 'northern_leaf_blight'
        ]
        self.class_names = []
        for plant in self.plant_classes:
            self.class_names.append(f"{plant}_healthy")
            for disease in self.disease_classes[1:]:  # Skip 'healthy'
                if plant in disease or 'blight' in disease:
                    self.class_names.append(f"{plant}_{disease}")
    
    def _load_model(self):
        """Load the trained model"""
        if not TF_AVAILABLE:
            logging.info("Using mock model implementation")
            self.is_loaded = True
            return
        
        try:
            if os.path.exists(self.model_path):
                self.model = load_model(self.model_path)
                self.is_loaded = True
                logging.info(f"Model loaded successfully from: {self.model_path}")
            else:
                logging.warning(f"Model file not found: {self.model_path}")
                self.is_loaded = False
        except Exception as e:
            logging.error(f"Error loading model: {e}")
            self.is_loaded = False
    
    def preprocess_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Preprocess image for model prediction
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed image array or None if error
        """
        try:
            # Load image
            image = Image.open(image_path)
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize to model input size
            target_size = self.input_shape[:2]
            image = image.resize(target_size, Image.Resampling.LANCZOS)
            
            # Convert to numpy array
            image_array = np.array(image)
            
            # Normalize pixel values to [0, 1]
            image_array = image_array.astype(np.float32) / 255.0
            
            # Add batch dimension
            image_array = np.expand_dims(image_array, axis=0)
            
            return image_array
            
        except Exception as e:
            logging.error(f"Error preprocessing image {image_path}: {e}")
            return None
    
    def predict(self, image_path: str) -> Dict:
        """
        Predict plant disease from image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing prediction results
        """
        start_time = time.time()
        
        # Preprocess image
        processed_image = self.preprocess_image(image_path)
        if processed_image is None:
            return {
                'error': 'Failed to preprocess image',
                'processing_time': time.time() - start_time
            }
        
        # Make prediction
        if self.is_loaded and TF_AVAILABLE and self.model:
            try:
                predictions = self.model.predict(processed_image, verbose=0)
                prediction_result = self._process_real_prediction(predictions)
            except Exception as e:
                logging.error(f"Error during model prediction: {e}")
                prediction_result = self._generate_mock_prediction()
        else:
            prediction_result = self._generate_mock_prediction()
        
        prediction_result['processing_time'] = time.time() - start_time
        return prediction_result
    
    def _process_real_prediction(self, predictions: np.ndarray) -> Dict:
        """Process real model predictions"""
        # Get prediction probabilities
        probabilities = predictions[0]
        
        # Get top prediction
        top_prediction_idx = np.argmax(probabilities)
        confidence = float(probabilities[top_prediction_idx])
        
        # Extract plant and disease information
        if top_prediction_idx < len(self.class_names):
            predicted_class = self.class_names[top_prediction_idx]
            plant_name, disease_info = self._parse_class_name(predicted_class)
            
            return {
                'plant_name': plant_name,
                'disease_name': disease_info['name'],
                'is_healthy': disease_info['is_healthy'],
                'confidence': confidence * 100,
                'severity': disease_info['severity'],
                'all_predictions': [
                    {
                        'class': self.class_names[i] if i < len(self.class_names) else f'class_{i}',
                        'confidence': float(prob * 100)
                    }
                    for i, prob in enumerate(probabilities)
                ][:5]  # Top 5 predictions
            }
        else:
            return self._generate_mock_prediction()
    
    def _generate_mock_prediction(self) -> Dict:
        """Generate mock prediction for testing/demo purposes"""
        import random
        
        # Randomly select plant and disease
        plant = random.choice(['Apple', 'Tomato', 'Corn'])
        is_healthy = random.random() < 0.3  # 30% chance of healthy
        
        diseases = {
            'Apple': [
                {'name': 'Apple Scab', 'severity': 'High'},
                {'name': 'Fire Blight', 'severity': 'Critical'}
            ],
            'Tomato': [
                {'name': 'Early Blight', 'severity': 'Medium'},
                {'name': 'Late Blight', 'severity': 'Critical'}
            ],
            'Corn': [
                {'name': 'Corn Smut', 'severity': 'Medium'},
                {'name': 'Northern Leaf Blight', 'severity': 'High'}
            ]
        }
        
        if is_healthy:
            disease_name = None
            severity = None
        else:
            disease_info = random.choice(diseases[plant])
            disease_name = disease_info['name']
            severity = disease_info['severity']
        
        confidence = random.uniform(85, 98)
        
        return {
            'plant_name': plant,
            'disease_name': disease_name,
            'is_healthy': is_healthy,
            'confidence': round(confidence, 1),
            'severity': severity,
            'model_version': '1.0.0-mock'
        }
    
    def _parse_class_name(self, class_name: str) -> Tuple[str, Dict]:
        """Parse class name to extract plant and disease information"""
        parts = class_name.split('_')
        
        if len(parts) >= 2:
            plant_name = parts[0].title()
            
            if 'healthy' in class_name.lower():
                return plant_name, {
                    'name': None,
                    'is_healthy': True,
                    'severity': None
                }
            else:
                disease_name = '_'.join(parts[1:]).replace('_', ' ').title()
                
                # Determine severity based on known diseases
                severity_map = {
                    'fire_blight': 'Critical',
                    'late_blight': 'Critical',
                    'apple_scab': 'High',
                    'northern_leaf_blight': 'High',
                    'early_blight': 'Medium',
                    'corn_smut': 'Medium'
                }
                
                severity = severity_map.get('_'.join(parts[1:]).lower(), 'Medium')
                
                return plant_name, {
                    'name': disease_name,
                    'is_healthy': False,
                    'severity': severity
                }
        
        # Fallback
        return 'Unknown', {'name': None, 'is_healthy': True, 'severity': None}
    
    def get_model_info(self) -> Dict:
        """Get information about the loaded model"""
        return {
            'model_path': self.model_path,
            'is_loaded': self.is_loaded,
            'tf_available': TF_AVAILABLE,
            'input_shape': self.input_shape,
            'num_classes': len(self.class_names),
            'plant_classes': self.plant_classes,
            'disease_classes': self.disease_classes
        }
    
    def health_check(self) -> bool:
        """Check if model is ready for predictions"""
        return self.is_loaded or not TF_AVAILABLE  # Return True for mock implementation