"""
Crop Disease Detection System - Helper Functions
General utility functions and helpers
"""

import os
import hashlib
import uuid
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from PIL import Image
import json
import re

def generate_unique_filename(original_filename: str, include_timestamp: bool = True) -> str:
    """
    Generate unique filename with optional timestamp
    
    Args:
        original_filename: Original file name
        include_timestamp: Whether to include timestamp
        
    Returns:
        Unique filename string
    """
    try:
        # Clean the filename
        cleaned_name = secure_filename_custom(original_filename)
        name, ext = os.path.splitext(cleaned_name)
        
        if include_timestamp:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # milliseconds
            unique_name = f"{name}_{timestamp}{ext}"
        else:
            # Use UUID for uniqueness
            unique_id = str(uuid.uuid4())[:8]
            unique_name = f"{name}_{unique_id}{ext}"
        
        return unique_name
        
    except Exception as e:
        logging.error(f"Error generating unique filename: {e}")
        # Fallback to UUID-based name
        fallback_ext = '.jpg'  # default extension
        return f"file_{str(uuid.uuid4())[:8]}{fallback_ext}"

def secure_filename_custom(filename: str) -> str:
    """
    Custom secure filename function with additional safety
    
    Args:
        filename: Original filename
        
    Returns:
        Secured filename
    """
    if not filename:
        return 'unnamed_file'
    
    # Remove directory path
    filename = os.path.basename(filename)
    
    # Replace spaces and special characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Ensure it doesn't start with a dot
    filename = filename.lstrip('.')
    
    # Limit length
    max_length = 200
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        name = name[:max_length - len(ext)]
        filename = name + ext
    
    return filename or 'unnamed_file'

def calculate_file_hash(file_path: str, algorithm: str = 'md5') -> str:
    """
    Calculate hash of file
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
        
    Returns:
        Hex digest of file hash
    """
    try:
        if algorithm == 'md5':
            hash_obj = hashlib.md5()
        elif algorithm == 'sha1':
            hash_obj = hashlib.sha1()
        elif algorithm == 'sha256':
            hash_obj = hashlib.sha256()
        else:
            hash_obj = hashlib.md5()  # default
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
        
    except Exception as e:
        logging.error(f"Error calculating file hash: {e}")
        return ""

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    
    return f"{s} {size_names[i]}"

def get_image_dimensions(image_path: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Get image dimensions
    
    Args:
        image_path: Path to image file
        
    Returns:
        Tuple of (width, height) or (None, None) if error
    """
    try:
        with Image.open(image_path) as img:
            return img.size  # (width, height)
    except Exception as e:
        logging.error(f"Error getting image dimensions: {e}")
        return None, None

def create_thumbnail(image_path: str, output_path: str, size: Tuple[int, int] = (150, 150), 
                    quality: int = 85) -> Dict:
    """
    Create thumbnail from image
    
    Args:
        image_path: Source image path
        output_path: Thumbnail output path
        size: Thumbnail size tuple
        quality: JPEG quality (1-100)
        
    Returns:
        Dictionary with operation results
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Calculate thumbnail size maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Create output directory if needed
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save thumbnail
            img.save(output_path, 'JPEG', quality=quality)
            
            return {
                'success': True,
                'thumbnail_path': output_path,
                'original_size': Image.open(image_path).size,
                'thumbnail_size': img.size
            }
            
    except Exception as e:
        logging.error(f"Error creating thumbnail: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def parse_confidence_score(confidence: Union[str, int, float]) -> float:
    """
    Parse and validate confidence score
    
    Args:
        confidence: Confidence value in various formats
        
    Returns:
        Normalized confidence score (0.0 to 1.0)
    """
    try:
        if isinstance(confidence, str):
            # Remove percentage sign if present
            confidence = confidence.replace('%', '').strip()
            confidence = float(confidence)
        
        confidence = float(confidence)
        
        # Convert percentage to decimal if needed
        if confidence > 1.0:
            confidence = confidence / 100.0
        
        # Clamp to valid range
        confidence = max(0.0, min(1.0, confidence))
        
        return confidence
        
    except (ValueError, TypeError):
        logging.warning(f"Invalid confidence score: {confidence}")
        return 0.0

def format_timestamp(timestamp: Union[datetime, float, int], format_str: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    Format timestamp to string
    
    Args:
        timestamp: Timestamp in various formats
        format_str: Output format string
        
    Returns:
        Formatted timestamp string
    """
    try:
        if isinstance(timestamp, datetime):
            dt = timestamp
        elif isinstance(timestamp, (int, float)):
            dt = datetime.fromtimestamp(timestamp)
        else:
            return str(timestamp)
        
        return dt.strftime(format_str)
        
    except Exception as e:
        logging.error(f"Error formatting timestamp: {e}")
        return str(timestamp)

def time_ago(timestamp: Union[datetime, float]) -> str:
    """
    Get human-readable time ago string
    
    Args:
        timestamp: Timestamp to compare
        
    Returns:
        Time ago string (e.g., "2 hours ago")
    """
    try:
        if isinstance(timestamp, datetime):
            dt = timestamp
        else:
            dt = datetime.fromtimestamp(timestamp)
        
        now = datetime.now()
        diff = now - dt
        
        seconds = int(diff.total_seconds())
        
        if seconds < 60:
            return "Just now"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif seconds < 2592000:  # 30 days
            days = seconds // 86400
            return f"{days} day{'s' if days != 1 else ''} ago"
        else:
            return dt.strftime('%Y-%m-%d')
        
    except Exception as e:
        logging.error(f"Error calculating time ago: {e}")
        return "Unknown"

def clean_text(text: str, max_length: int = None) -> str:
    """
    Clean and normalize text
    
    Args:
        text: Input text
        max_length: Maximum length limit
        
    Returns:
        Cleaned text
    """
    if not isinstance(text, str):
        return ""
    
    # Basic cleaning
    cleaned = text.strip()
    
    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Remove control characters
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', cleaned)
    
    # Apply length limit
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rsplit(' ', 1)[0] + '...'
    
    return cleaned

def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text
    
    Args:
        text: Input text
        min_length: Minimum keyword length
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of extracted keywords
    """
    try:
        if not isinstance(text, str):
            return []
        
        # Convert to lowercase and remove punctuation
        cleaned_text = re.sub(r'[^\w\s]', ' ', text.lower())
        
        # Split into words
        words = cleaned_text.split()
        
        # Filter words by length and common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
        }
        
        keywords = []
        for word in words:
            if len(word) >= min_length and word not in stop_words:
                keywords.append(word)
        
        # Remove duplicates while preserving order
        unique_keywords = []
        seen = set()
        for keyword in keywords:
            if keyword not in seen:
                unique_keywords.append(keyword)
                seen.add(keyword)
        
        return unique_keywords[:max_keywords]
        
    except Exception as e:
        logging.error(f"Error extracting keywords: {e}")
        return []

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts using Jaccard similarity
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score (0.0 to 1.0)
    """
    try:
        if not isinstance(text1, str) or not isinstance(text2, str):
            return 0.0
        
        # Extract keywords from both texts
        keywords1 = set(extract_keywords(text1))
        keywords2 = set(extract_keywords(text2))
        
        if not keywords1 and not keywords2:
            return 1.0  # Both empty
        
        if not keywords1 or not keywords2:
            return 0.0  # One empty
        
        # Calculate Jaccard similarity
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0
        
    except Exception as e:
        logging.error(f"Error calculating similarity: {e}")
        return 0.0

def paginate_list(items: List[Any], page: int, per_page: int) -> Dict:
    """
    Paginate a list of items
    
    Args:
        items: List of items to paginate
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Dictionary with pagination info
    """
    try:
        total_items = len(items)
        total_pages = math.ceil(total_items / per_page)
        
        # Validate page number
        page = max(1, min(page, total_pages)) if total_pages > 0 else 1
        
        # Calculate slice indices
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        # Get items for current page
        page_items = items[start_idx:end_idx]
        
        return {
            'items': page_items,
            'page': page,
            'per_page': per_page,
            'total_items': total_items,
            'total_pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_page': page - 1 if page > 1 else None,
            'next_page': page + 1 if page < total_pages else None
        }
        
    except Exception as e:
        logging.error(f"Error paginating list: {e}")
        return {
            'items': [],
            'page': 1,
            'per_page': per_page,
            'total_items': 0,
            'total_pages': 0,
            'has_prev': False,
            'has_next': False,
            'prev_page': None,
            'next_page': None
        }

def create_response_dict(success: bool, data: Any = None, error: str = None, 
                        code: str = None, **kwargs) -> Dict:
    """
    Create standardized response dictionary
    
    Args:
        success: Success status
        data: Response data
        error: Error message
        code: Error code
        **kwargs: Additional fields
        
    Returns:
        Standardized response dictionary
    """
    response = {
        'success': success,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if success:
        if data is not None:
            response['data'] = data
    else:
        if error:
            response['error'] = error
        if code:
            response['code'] = code
    
    # Add any additional fields
    response.update(kwargs)
    
    return response

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with fallback
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON data or default value
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def safe_json_dumps(data: Any, default: str = '{}') -> str:
    """
    Safely serialize data to JSON with fallback
    
    Args:
        data: Data to serialize
        default: Default JSON string if serialization fails
        
    Returns:
        JSON string or default value
    """
    try:
        return json.dumps(data, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return default

def flatten_dict(nested_dict: Dict, separator: str = '.', parent_key: str = '') -> Dict:
    """
    Flatten nested dictionary
    
    Args:
        nested_dict: Nested dictionary to flatten
        separator: Key separator
        parent_key: Parent key prefix
        
    Returns:
        Flattened dictionary
    """
    items = []
    
    for key, value in nested_dict.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        
        if isinstance(value, dict):
            items.extend(flatten_dict(value, separator, new_key).items())
        else:
            items.append((new_key, value))
    
    return dict(items)

def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split list into chunks
    
    Args:
        lst: List to chunk
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    if chunk_size <= 0:
        return [lst]
    
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def merge_dicts(*dicts: Dict) -> Dict:
    """
    Merge multiple dictionaries
    
    Args:
        *dicts: Dictionaries to merge
        
    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result

def get_nested_value(data: Dict, key_path: str, default: Any = None, separator: str = '.') -> Any:
    """
    Get value from nested dictionary using dot notation
    
    Args:
        data: Nested dictionary
        key_path: Dot-separated key path (e.g., 'user.profile.name')
        default: Default value if key not found
        separator: Key separator
        
    Returns:
        Value at key path or default
    """
    try:
        keys = key_path.split(separator)
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
        
    except Exception:
        return default

def set_nested_value(data: Dict, key_path: str, value: Any, separator: str = '.') -> Dict:
    """
    Set value in nested dictionary using dot notation
    
    Args:
        data: Nested dictionary
        key_path: Dot-separated key path
        value: Value to set
        separator: Key separator
        
    Returns:
        Modified dictionary
    """
    keys = key_path.split(separator)
    current = data
    
    for key in keys[:-1]:
        if key not in current or not isinstance(current[key], dict):
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
    return data

def validate_and_convert_types(data: Dict, schema: Dict) -> Dict:
    """
    Validate and convert data types based on schema
    
    Args:
        data: Data dictionary to validate
        schema: Schema with field names and expected types
        
    Returns:
        Dictionary with converted values
    """
    result = {}
    errors = []
    
    for field, expected_type in schema.items():
        if field in data:
            value = data[field]
            
            try:
                if expected_type == int:
                    result[field] = int(value)
                elif expected_type == float:
                    result[field] = float(value)
                elif expected_type == bool:
                    if isinstance(value, str):
                        result[field] = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        result[field] = bool(value)
                elif expected_type == str:
                    result[field] = str(value)
                elif expected_type == list:
                    if isinstance(value, str):
                        # Try to parse as JSON array
                        try:
                            result[field] = json.loads(value)
                        except:
                            # Split by comma if not JSON
                            result[field] = [item.strip() for item in value.split(',')]
                    else:
                        result[field] = list(value) if value else []
                else:
                    result[field] = value
                    
            except (ValueError, TypeError) as e:
                errors.append(f"Invalid type for field '{field}': {str(e)}")
    
    if errors:
        raise ValueError(f"Type validation errors: {'; '.join(errors)}")
    
    return result

def generate_slug(text: str, max_length: int = 50) -> str:
    """
    Generate URL-friendly slug from text
    
    Args:
        text: Input text
        max_length: Maximum slug length
        
    Returns:
        URL-friendly slug
    """
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase and remove special characters
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    
    # Replace spaces and multiple hyphens with single hyphen
    slug = re.sub(r'[\s_-]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Apply length limit
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    return slug or 'item'

def format_duration(seconds: Union[int, float]) -> str:
    """
    Format duration in seconds to human readable string
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    try:
        seconds = int(seconds)
        
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds}s"
        else:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            return f"{hours}h {remaining_minutes}m"
            
    except (ValueError, TypeError):
        return "0s"

def calculate_percentage(value: Union[int, float], total: Union[int, float], 
                        decimal_places: int = 1) -> float:
    """
    Calculate percentage with error handling
    
    Args:
        value: Numerator value
        total: Denominator value
        decimal_places: Number of decimal places
        
    Returns:
        Percentage value
    """
    try:
        if total == 0:
            return 0.0
        
        percentage = (value / total) * 100
        return round(percentage, decimal_places)
        
    except (ValueError, TypeError, ZeroDivisionError):
        return 0.0

def retry_on_failure(func, max_attempts: int = 3, delay: float = 1.0, 
                    backoff_factor: float = 2.0):
    """
    Retry function on failure with exponential backoff
    
    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        delay: Initial delay between attempts
        backoff_factor: Backoff multiplier
        
    Returns:
        Function result or raises last exception
    """
    import time
    
    last_exception = None
    current_delay = delay
    
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            last_exception = e
            
            if attempt < max_attempts - 1:  # Don't sleep on last attempt
                time.sleep(current_delay)
                current_delay *= backoff_factor
            else:
                break
    
    # If we get here, all attempts failed
    raise last_exception

def get_client_ip(request) -> str:
    """
    Get client IP address from request
    
    Args:
        request: Flask request object
        
    Returns:
        Client IP address
    """
    try:
        # Check for forwarded IP (behind proxy)
        if 'X-Forwarded-For' in request.headers:
            return request.headers['X-Forwarded-For'].split(',')[0].strip()
        elif 'X-Real-IP' in request.headers:
            return request.headers['X-Real-IP']
        else:
            return request.remote_addr or 'unknown'
    except Exception:
        return 'unknown'

def is_mobile_device(user_agent: str) -> bool:
    """
    Check if user agent indicates mobile device
    
    Args:
        user_agent: User agent string
        
    Returns:
        True if mobile device
    """
    if not user_agent:
        return False
    
    mobile_keywords = [
        'mobile', 'android', 'iphone', 'ipad', 'tablet', 'phone',
        'blackberry', 'webos', 'opera mini', 'windows phone'
    ]
    
    user_agent_lower = user_agent.lower()
    return any(keyword in user_agent_lower for keyword in mobile_keywords)

def truncate_text(text: str, max_length: int, suffix: str = '...') -> str:
    """
    Truncate text to maximum length with suffix
    
    Args:
        text: Input text
        max_length: Maximum length including suffix
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if not isinstance(text, str) or len(text) <= max_length:
        return text
    
    if len(suffix) >= max_length:
        return text[:max_length]
    
    truncated_length = max_length - len(suffix)
    return text[:truncated_length] + suffix