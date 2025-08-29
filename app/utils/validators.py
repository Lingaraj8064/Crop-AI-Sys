"""
Crop Disease Detection System - Validators
Input validation utilities for various data types
"""

import re
import os
import logging
from typing import Dict, List, Optional, Any, Union
from werkzeug.datastructures import FileStorage
from PIL import Image
import json

def validate_image_file(file: FileStorage) -> Dict:
    """
    Validate uploaded image file
    
    Args:
        file: FileStorage object from Flask
        
    Returns:
        Dictionary with validation results
    """
    try:
        # Check if file exists
        if not file or file.filename == '':
            return {
                'valid': False,
                'error': 'No file provided',
                'code': 'NO_FILE'
            }
        
        # Allowed configurations
        ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        ALLOWED_MIME_TYPES = {
            'image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 
            'image/gif', 'image/tiff', 'image/webp'
        }
        MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
        MIN_FILE_SIZE = 1024  # 1KB
        MAX_DIMENSIONS = (4000, 4000)
        MIN_DIMENSIONS = (100, 100)
        
        # Validate filename
        filename = file.filename
        if not filename or len(filename.strip()) == 0:
            return {
                'valid': False,
                'error': 'Invalid filename',
                'code': 'INVALID_FILENAME'
            }
        
        # Check file extension
        file_extension = os.path.splitext(filename)[1].lower()
        if file_extension not in ALLOWED_EXTENSIONS:
            return {
                'valid': False,
                'error': f'Unsupported file extension: {file_extension}. Allowed: {", ".join(ALLOWED_EXTENSIONS)}',
                'code': 'UNSUPPORTED_EXTENSION'
            }
        
        # Check MIME type
        if file.mimetype and file.mimetype not in ALLOWED_MIME_TYPES:
            return {
                'valid': False,
                'error': f'Unsupported MIME type: {file.mimetype}',
                'code': 'UNSUPPORTED_MIME_TYPE'
            }
        
        # Check file size if available in headers
        if hasattr(file, 'content_length') and file.content_length:
            if file.content_length > MAX_FILE_SIZE:
                return {
                    'valid': False,
                    'error': f'File too large: {file.content_length} bytes. Maximum: {MAX_FILE_SIZE} bytes',
                    'code': 'FILE_TOO_LARGE'
                }
            
            if file.content_length < MIN_FILE_SIZE:
                return {
                    'valid': False,
                    'error': f'File too small: {file.content_length} bytes. Minimum: {MIN_FILE_SIZE} bytes',
                    'code': 'FILE_TOO_SMALL'
                }
        
        # Try to validate actual image content
        try:
            file.stream.seek(0)  # Reset file pointer
            with Image.open(file.stream) as img:
                # Check image dimensions
                width, height = img.size
                
                if width > MAX_DIMENSIONS[0] or height > MAX_DIMENSIONS[1]:
                    return {
                        'valid': False,
                        'error': f'Image too large: {width}x{height}. Maximum: {MAX_DIMENSIONS[0]}x{MAX_DIMENSIONS[1]}',
                        'code': 'IMAGE_TOO_LARGE'
                    }
                
                if width < MIN_DIMENSIONS[0] or height < MIN_DIMENSIONS[1]:
                    return {
                        'valid': False,
                        'error': f'Image too small: {width}x{height}. Minimum: {MIN_DIMENSIONS[0]}x{MIN_DIMENSIONS[1]}',
                        'code': 'IMAGE_TOO_SMALL'
                    }
                
                # Check if image mode is supported
                if img.mode not in ['RGB', 'RGBA', 'L', 'P']:
                    return {
                        'valid': False,
                        'error': f'Unsupported image mode: {img.mode}',
                        'code': 'UNSUPPORTED_MODE'
                    }
                
                # Verify image integrity
                img.verify()
                
            file.stream.seek(0)  # Reset file pointer again
            
        except Exception as img_error:
            return {
                'valid': False,
                'error': f'Invalid or corrupted image: {str(img_error)}',
                'code': 'CORRUPTED_IMAGE'
            }
        
        return {
            'valid': True,
            'filename': filename,
            'extension': file_extension,
            'mime_type': file.mimetype
        }
        
    except Exception as e:
        logging.error(f"Error validating image file: {e}")
        return {
            'valid': False,
            'error': 'Validation error occurred',
            'code': 'VALIDATION_ERROR'
        }

def validate_plant_data(plant_data: Dict) -> Dict:
    """
    Validate plant data structure
    
    Args:
        plant_data: Dictionary containing plant information
        
    Returns:
        Dictionary with validation results
    """
    try:
        required_fields = [
            'common_name', 'scientific_name', 'family', 'category',
            'soil_requirements', 'weather_requirements', 'care_instructions'
        ]
        
        errors = []
        
        # Check required fields
        for field in required_fields:
            if field not in plant_data:
                errors.append(f'Missing required field: {field}')
            elif not plant_data[field]:
                errors.append(f'Empty required field: {field}')
        
        if errors:
            return {
                'valid': False,
                'errors': errors,
                'code': 'MISSING_REQUIRED_FIELDS'
            }
        
        # Validate specific fields
        validation_errors = []
        
        # Validate names
        if not validate_plant_name(plant_data['common_name']):
            validation_errors.append('Invalid common name format')
        
        if not validate_scientific_name(plant_data['scientific_name']):
            validation_errors.append('Invalid scientific name format')
        
        # Validate category
        valid_categories = ['Fruit', 'Vegetable', 'Grain', 'Herb', 'Tree', 'Legume']
        if plant_data['category'] not in valid_categories:
            validation_errors.append(f'Invalid category. Must be one of: {", ".join(valid_categories)}')
        
        # Validate soil requirements
        soil_validation = validate_soil_requirements(plant_data['soil_requirements'])
        if not soil_validation['valid']:
            validation_errors.extend([f'Soil requirements: {err}' for err in soil_validation['errors']])
        
        # Validate weather requirements
        weather_validation = validate_weather_requirements(plant_data['weather_requirements'])
        if not weather_validation['valid']:
            validation_errors.extend([f'Weather requirements: {err}' for err in weather_validation['errors']])
        
        # Validate care instructions
        care_validation = validate_care_instructions(plant_data['care_instructions'])
        if not care_validation['valid']:
            validation_errors.extend([f'Care instructions: {err}' for err in care_validation['errors']])
        
        # Validate diseases if present
        if 'diseases' in plant_data and plant_data['diseases']:
            for i, disease in enumerate(plant_data['diseases']):
                disease_validation = validate_disease_data(disease)
                if not disease_validation['valid']:
                    validation_errors.extend([f'Disease {i+1}: {err}' for err in disease_validation['errors']])
        
        if validation_errors:
            return {
                'valid': False,
                'errors': validation_errors,
                'code': 'VALIDATION_ERRORS'
            }
        
        return {
            'valid': True,
            'message': 'Plant data is valid'
        }
        
    except Exception as e:
        logging.error(f"Error validating plant data: {e}")
        return {
            'valid': False,
            'errors': [f'Validation error: {str(e)}'],
            'code': 'VALIDATION_ERROR'
        }

def validate_disease_data(disease_data: Dict) -> Dict:
    """
    Validate disease data structure
    
    Args:
        disease_data: Dictionary containing disease information
        
    Returns:
        Dictionary with validation results
    """
    try:
        required_fields = [
            'name', 'severity', 'type', 'symptoms', 'causes', 
            'prevention', 'treatment', 'immediate_action'
        ]
        
        errors = []
        
        # Check required fields
        for field in required_fields:
            if field not in disease_data:
                errors.append(f'Missing required field: {field}')
            elif not disease_data[field]:
                errors.append(f'Empty required field: {field}')
        
        if errors:
            return {
                'valid': False,
                'errors': errors,
                'code': 'MISSING_REQUIRED_FIELDS'
            }
        
        validation_errors = []
        
        # Validate disease name
        if not validate_disease_name(disease_data['name']):
            validation_errors.append('Invalid disease name format')
        
        # Validate severity
        valid_severities = ['Low', 'Medium', 'High', 'Critical']
        if disease_data['severity'] not in valid_severities:
            validation_errors.append(f'Invalid severity. Must be one of: {", ".join(valid_severities)}')
        
        # Validate disease type
        valid_types = ['fungal', 'bacterial', 'viral', 'nutritional', 'environmental', 'pest']
        if disease_data['type'] not in valid_types:
            validation_errors.append(f'Invalid disease type. Must be one of: {", ".join(valid_types)}')
        
        # Validate text fields
        text_fields = ['symptoms', 'causes', 'immediate_action']
        for field in text_fields:
            if len(disease_data[field].strip()) < 10:
                validation_errors.append(f'{field} must be at least 10 characters long')
        
        # Validate list fields
        list_fields = ['prevention', 'treatment']
        for field in list_fields:
            if not isinstance(disease_data[field], list):
                validation_errors.append(f'{field} must be a list')
            elif len(disease_data[field]) == 0:
                validation_errors.append(f'{field} cannot be empty')
            elif any(not item.strip() for item in disease_data[field]):
                validation_errors.append(f'{field} contains empty items')
        
        # Validate optional fields
        if 'scientific_name' in disease_data and disease_data['scientific_name']:
            if not validate_scientific_name(disease_data['scientific_name']):
                validation_errors.append('Invalid scientific name format')
        
        if 'contagious_level' in disease_data:
            valid_contagious_levels = ['Low', 'Medium', 'High']
            if disease_data['contagious_level'] not in valid_contagious_levels:
                validation_errors.append(f'Invalid contagious level. Must be one of: {", ".join(valid_contagious_levels)}')
        
        if validation_errors:
            return {
                'valid': False,
                'errors': validation_errors,
                'code': 'VALIDATION_ERRORS'
            }
        
        return {
            'valid': True,
            'message': 'Disease data is valid'
        }
        
    except Exception as e:
        logging.error(f"Error validating disease data: {e}")
        return {
            'valid': False,
            'errors': [f'Validation error: {str(e)}'],
            'code': 'VALIDATION_ERROR'
        }

def validate_soil_requirements(soil_data: Dict) -> Dict:
    """Validate soil requirements data"""
    try:
        required_fields = ['ph_min', 'ph_max', 'drainage', 'nutrients', 'organic_matter', 'depth_requirement']
        errors = []
        
        for field in required_fields:
            if field not in soil_data:
                errors.append(f'Missing field: {field}')
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        validation_errors = []
        
        # Validate pH range
        try:
            ph_min = float(soil_data['ph_min'])
            ph_max = float(soil_data['ph_max'])
            
            if not (0 <= ph_min <= 14) or not (0 <= ph_max <= 14):
                validation_errors.append('pH values must be between 0 and 14')
            
            if ph_min >= ph_max:
                validation_errors.append('pH minimum must be less than pH maximum')
                
        except (ValueError, TypeError):
            validation_errors.append('Invalid pH values - must be numeric')
        
        # Validate drainage
        valid_drainage = ['well-draining', 'poorly-draining', 'moderate drainage']
        drainage_lower = soil_data['drainage'].lower()
        if not any(valid in drainage_lower for valid in valid_drainage):
            validation_errors.append('Invalid drainage description')
        
        # Validate nutrients
        if not isinstance(soil_data['nutrients'], list) or len(soil_data['nutrients']) == 0:
            validation_errors.append('Nutrients must be a non-empty list')
        
        return {
            'valid': len(validation_errors) == 0,
            'errors': validation_errors
        }
        
    except Exception as e:
        return {'valid': False, 'errors': [f'Soil validation error: {str(e)}']}

def validate_weather_requirements(weather_data: Dict) -> Dict:
    """Validate weather requirements data"""
    try:
        required_fields = [
            'temp_min', 'temp_max', 'temp_optimal_min', 'temp_optimal_max',
            'rainfall_min', 'rainfall_max', 'humidity_range', 'sunlight_hours', 'frost_tolerance'
        ]
        errors = []
        
        for field in required_fields:
            if field not in weather_data:
                errors.append(f'Missing field: {field}')
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        validation_errors = []
        
        # Validate temperature ranges
        try:
            temp_fields = ['temp_min', 'temp_max', 'temp_optimal_min', 'temp_optimal_max']
            temps = {field: float(weather_data[field]) for field in temp_fields}
            
            if temps['temp_min'] >= temps['temp_max']:
                validation_errors.append('Minimum temperature must be less than maximum')
            
            if temps['temp_optimal_min'] >= temps['temp_optimal_max']:
                validation_errors.append('Optimal minimum temperature must be less than optimal maximum')
            
            if not (temps['temp_min'] <= temps['temp_optimal_min'] <= temps['temp_optimal_max'] <= temps['temp_max']):
                validation_errors.append('Temperature ranges must be logically ordered')
                
        except (ValueError, TypeError):
            validation_errors.append('Invalid temperature values - must be numeric')
        
        # Validate rainfall
        try:
            rainfall_min = float(weather_data['rainfall_min'])
            rainfall_max = float(weather_data['rainfall_max'])
            
            if rainfall_min < 0 or rainfall_max < 0:
                validation_errors.append('Rainfall values cannot be negative')
            
            if rainfall_min >= rainfall_max:
                validation_errors.append('Minimum rainfall must be less than maximum')
                
        except (ValueError, TypeError):
            validation_errors.append('Invalid rainfall values - must be numeric')
        
        # Validate sunlight hours
        sunlight = weather_data['sunlight_hours']
        if not isinstance(sunlight, str) or len(sunlight.strip()) == 0:
            validation_errors.append('Sunlight hours must be a non-empty string')
        
        return {
            'valid': len(validation_errors) == 0,
            'errors': validation_errors
        }
        
    except Exception as e:
        return {'valid': False, 'errors': [f'Weather validation error: {str(e)}']}

def validate_care_instructions(care_data: Dict) -> Dict:
    """Validate care instructions data"""
    try:
        required_fields = ['watering', 'fertilization', 'pruning', 'pest_management', 'harvesting']
        errors = []
        
        for field in required_fields:
            if field not in care_data:
                errors.append(f'Missing field: {field}')
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        validation_errors = []
        
        # Validate list fields
        list_fields = ['watering', 'fertilization', 'pruning', 'pest_management']
        for field in list_fields:
            if not isinstance(care_data[field], list):
                validation_errors.append(f'{field} must be a list')
            elif len(care_data[field]) == 0:
                validation_errors.append(f'{field} cannot be empty')
            elif any(not str(item).strip() for item in care_data[field]):
                validation_errors.append(f'{field} contains empty items')
        
        # Validate harvesting (string field)
        if not isinstance(care_data['harvesting'], str) or len(care_data['harvesting'].strip()) == 0:
            validation_errors.append('Harvesting information must be a non-empty string')
        
        return {
            'valid': len(validation_errors) == 0,
            'errors': validation_errors
        }
        
    except Exception as e:
        return {'valid': False, 'errors': [f'Care instructions validation error: {str(e)}']}

def validate_plant_name(name: str) -> bool:
    """Validate plant common name format"""
    if not isinstance(name, str) or len(name.strip()) < 2:
        return False
    
    # Allow letters, spaces, hyphens, and apostrophes
    pattern = r"^[A-Za-z\s\-']+$"
    return bool(re.match(pattern, name.strip()))

def validate_scientific_name(name: str) -> bool:
    """Validate scientific name format (Genus species)"""
    if not isinstance(name, str) or len(name.strip()) < 3:
        return False
    
    # Scientific names should follow binomial nomenclature
    pattern = r"^[A-Z][a-z]+ [a-z]+( [a-z]+)*$"
    return bool(re.match(pattern, name.strip()))

def validate_disease_name(name: str) -> bool:
    """Validate disease name format"""
    if not isinstance(name, str) or len(name.strip()) < 2:
        return False
    
    # Allow letters, spaces, hyphens, apostrophes, and parentheses
    pattern = r"^[A-Za-z\s\-'()]+$"
    return bool(re.match(pattern, name.strip()))

def validate_email(email: str) -> bool:
    """Validate email address format"""
    if not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}
    return bool(re.match(pattern, email.strip()))

def validate_url(url: str) -> bool:
    """Validate URL format"""
    if not isinstance(url, str):
        return False
    
    pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?
    return bool(re.match(pattern, url.strip()))

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format (basic validation)"""
    if not isinstance(phone, str):
        return False
    
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Check if remaining characters are digits and reasonable length
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15

def validate_json_data(data: Union[str, Dict]) -> Dict:
    """Validate JSON data structure"""
    try:
        if isinstance(data, str):
            parsed_data = json.loads(data)
        elif isinstance(data, dict):
            parsed_data = data
        else:
            return {
                'valid': False,
                'error': 'Data must be a string or dictionary',
                'code': 'INVALID_DATA_TYPE'
            }
        
        return {
            'valid': True,
            'data': parsed_data
        }
        
    except json.JSONDecodeError as e:
        return {
            'valid': False,
            'error': f'Invalid JSON format: {str(e)}',
            'code': 'INVALID_JSON'
        }
    except Exception as e:
        return {
            'valid': False,
            'error': f'Validation error: {str(e)}',
            'code': 'VALIDATION_ERROR'
        }

def validate_coordinate(lat: float, lng: float) -> Dict:
    """Validate geographic coordinates"""
    try:
        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
            return {
                'valid': False,
                'error': 'Coordinates must be numeric',
                'code': 'INVALID_COORDINATE_TYPE'
            }
        
        if not (-90 <= lat <= 90):
            return {
                'valid': False,
                'error': 'Latitude must be between -90 and 90',
                'code': 'INVALID_LATITUDE'
            }
        
        if not (-180 <= lng <= 180):
            return {
                'valid': False,
                'error': 'Longitude must be between -180 and 180',
                'code': 'INVALID_LONGITUDE'
            }
        
        return {
            'valid': True,
            'latitude': lat,
            'longitude': lng
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Coordinate validation error: {str(e)}',
            'code': 'VALIDATION_ERROR'
        }

def validate_date_range(start_date: str, end_date: str, date_format: str = '%Y-%m-%d') -> Dict:
    """Validate date range"""
    try:
        from datetime import datetime
        
        start = datetime.strptime(start_date, date_format)
        end = datetime.strptime(end_date, date_format)
        
        if start >= end:
            return {
                'valid': False,
                'error': 'Start date must be before end date',
                'code': 'INVALID_DATE_RANGE'
            }
        
        return {
            'valid': True,
            'start_date': start,
            'end_date': end
        }
        
    except ValueError as e:
        return {
            'valid': False,
            'error': f'Invalid date format: {str(e)}',
            'code': 'INVALID_DATE_FORMAT'
        }
    except Exception as e:
        return {
            'valid': False,
            'error': f'Date validation error: {str(e)}',
            'code': 'VALIDATION_ERROR'
        }

def sanitize_string(input_string: str, max_length: int = None, allowed_chars: str = None) -> str:
    """Sanitize string input"""
    if not isinstance(input_string, str):
        return ""
    
    # Basic sanitization
    sanitized = input_string.strip()
    
    # Remove or replace dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Apply character restrictions if specified
    if allowed_chars:
        sanitized = ''.join(char for char in sanitized if char in allowed_chars)
    
    # Apply length limit
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized

def validate_pagination_params(page: Any, per_page: Any, max_per_page: int = 100) -> Dict:
    """Validate pagination parameters"""
    try:
        # Convert and validate page
        try:
            page_num = int(page) if page is not None else 1
        except (ValueError, TypeError):
            page_num = 1
        
        if page_num < 1:
            page_num = 1
        
        # Convert and validate per_page
        try:
            per_page_num = int(per_page) if per_page is not None else 20
        except (ValueError, TypeError):
            per_page_num = 20
        
        if per_page_num < 1:
            per_page_num = 20
        elif per_page_num > max_per_page:
            per_page_num = max_per_page
        
        return {
            'valid': True,
            'page': page_num,
            'per_page': per_page_num,
            'offset': (page_num - 1) * per_page_num
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Pagination validation error: {str(e)}',
            'code': 'PAGINATION_ERROR'
        }

def validate_search_query(query: str, min_length: int = 2, max_length: int = 100) -> Dict:
    """Validate search query"""
    try:
        if not isinstance(query, str):
            return {
                'valid': False,
                'error': 'Query must be a string',
                'code': 'INVALID_QUERY_TYPE'
            }
        
        cleaned_query = query.strip()
        
        if len(cleaned_query) < min_length:
            return {
                'valid': False,
                'error': f'Query must be at least {min_length} characters long',
                'code': 'QUERY_TOO_SHORT'
            }
        
        if len(cleaned_query) > max_length:
            return {
                'valid': False,
                'error': f'Query must be no more than {max_length} characters long',
                'code': 'QUERY_TOO_LONG'
            }
        
        # Remove potentially dangerous characters
        sanitized_query = sanitize_string(cleaned_query, max_length)
        
        return {
            'valid': True,
            'query': sanitized_query,
            'original_query': query
        }
        
    except Exception as e:
        return {
            'valid': False,
            'error': f'Query validation error: {str(e)}',
            'code': 'VALIDATION_ERROR'
        }