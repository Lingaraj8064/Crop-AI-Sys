"""
Crop Disease Detection System - Image Processing Service
Service for image preprocessing, validation, and quality assessment
"""

import os
import logging
from typing import Dict, Tuple, Optional, List
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ExifTags
import cv2

class ImageProcessor:
    """Service class for image processing operations"""
    
    def __init__(self):
        """Initialize the image processor"""
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        self.max_file_size = 16 * 1024 * 1024  # 16MB
        self.target_size = (224, 224)  # Standard input size for models
        self.quality_thresholds = {
            'blur_threshold': 100,
            'brightness_min': 50,
            'brightness_max': 200,
            'contrast_min': 20
        }
    
    def validate_image(self, image_path: str) -> Dict:
        """
        Validate image file for processing
        
        Args:
            image_path: Path to image file
            
        Returns:
            Validation result dictionary
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return {
                    'valid': False,
                    'error': 'Image file not found',
                    'code': 'FILE_NOT_FOUND'
                }
            
            # Check file size
            file_size = os.path.getsize(image_path)
            if file_size > self.max_file_size:
                return {
                    'valid': False,
                    'error': f'File too large. Maximum size: {self.max_file_size / (1024*1024):.1f}MB',
                    'code': 'FILE_TOO_LARGE'
                }
            
            if file_size < 1024:  # Less than 1KB
                return {
                    'valid': False,
                    'error': 'File too small or corrupted',
                    'code': 'FILE_TOO_SMALL'
                }
            
            # Check file extension
            file_ext = os.path.splitext(image_path)[1].lower()
            if file_ext not in self.supported_formats:
                return {
                    'valid': False,
                    'error': f'Unsupported format. Supported: {", ".join(self.supported_formats)}',
                    'code': 'UNSUPPORTED_FORMAT'
                }
            
            # Try to open and validate image
            try:
                with Image.open(image_path) as img:
                    # Check image mode
                    if img.mode not in ['RGB', 'RGBA', 'L', 'P']:
                        return {
                            'valid': False,
                            'error': 'Unsupported image mode',
                            'code': 'UNSUPPORTED_MODE'
                        }
                    
                    # Check image dimensions
                    width, height = img.size
                    if width < 100 or height < 100:
                        return {
                            'valid': False,
                            'error': 'Image too small (minimum 100x100 pixels)',
                            'code': 'IMAGE_TOO_SMALL'
                        }
                    
                    if width > 4000 or height > 4000:
                        return {
                            'valid': False,
                            'error': 'Image too large (maximum 4000x4000 pixels)',
                            'code': 'IMAGE_TOO_LARGE'
                        }
                    
                    # Verify image can be loaded properly
                    img.verify()
            
            except Exception as img_error:
                return {
                    'valid': False,
                    'error': f'Invalid or corrupted image file: {str(img_error)}',
                    'code': 'CORRUPTED_IMAGE'
                }
            
            return {
                'valid': True,
                'file_size': file_size,
                'format': file_ext,
                'dimensions': (width, height)
            }
            
        except Exception as e:
            logging.error(f"Error validating image {image_path}: {e}")
            return {
                'valid': False,
                'error': 'Error during image validation',
                'code': 'VALIDATION_ERROR'
            }
    
    def preprocess_for_analysis(self, image_path: str, options: Dict = None) -> Dict:
        """
        Preprocess image for AI model analysis
        
        Args:
            image_path: Path to input image
            options: Processing options
            
        Returns:
            Processing result dictionary
        """
        try:
            options = options or {}
            
            # Validate image first
            validation_result = self.validate_image(image_path)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'code': validation_result['code']
                }
            
            # Load image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Handle EXIF orientation
                img = self._correct_image_orientation(img)
                
                # Apply preprocessing steps
                processed_img = self._apply_preprocessing_pipeline(img, options)
                
                # Save processed image if requested
                output_path = options.get('output_path')
                if output_path:
                    processed_img.save(output_path, 'JPEG', quality=95)
                
                return {
                    'success': True,
                    'original_size': img.size,
                    'processed_size': processed_img.size,
                    'output_path': output_path,
                    'preprocessing_applied': self._get_applied_preprocessing(options)
                }
                
        except Exception as e:
            logging.error(f"Error preprocessing image {image_path}: {e}")
            return {
                'success': False,
                'error': 'Image preprocessing failed',
                'code': 'PREPROCESSING_ERROR'
            }
    
    def _correct_image_orientation(self, img: Image.Image) -> Image.Image:
        """Correct image orientation based on EXIF data"""
        try:
            if hasattr(img, '_getexif'):
                exif = img._getexif()
                if exif is not None:
                    orientation_key = None
                    for tag, value in ExifTags.TAGS.items():
                        if value == 'Orientation':
                            orientation_key = tag
                            break
                    
                    if orientation_key and orientation_key in exif:
                        orientation = exif[orientation_key]
                        
                        if orientation == 3:
                            img = img.rotate(180, expand=True)
                        elif orientation == 6:
                            img = img.rotate(270, expand=True)
                        elif orientation == 8:
                            img = img.rotate(90, expand=True)
            
            return img
            
        except Exception as e:
            logging.warning(f"Could not correct image orientation: {e}")
            return img
    
    def _apply_preprocessing_pipeline(self, img: Image.Image, options: Dict) -> Image.Image:
        """Apply preprocessing pipeline to image"""
        processed_img = img.copy()
        
        # Resize if needed
        if options.get('resize', True):
            target_size = options.get('target_size', self.target_size)
            processed_img = self._smart_resize(processed_img, target_size)
        
        # Enhance image quality
        if options.get('enhance_quality', True):
            processed_img = self._enhance_image_quality(processed_img)
        
        # Apply filters
        if options.get('apply_filters', False):
            processed_img = self._apply_image_filters(processed_img, options)
        
        # Normalize colors
        if options.get('normalize_colors', True):
            processed_img = self._normalize_colors(processed_img)
        
        return processed_img
    
    def _smart_resize(self, img: Image.Image, target_size: Tuple[int, int]) -> Image.Image:
        """Intelligently resize image maintaining aspect ratio when possible"""
        original_width, original_height = img.size
        target_width, target_height = target_size
        
        # Calculate aspect ratios
        original_ratio = original_width / original_height
        target_ratio = target_width / target_height
        
        if abs(original_ratio - target_ratio) < 0.1:
            # Aspect ratios are similar, direct resize
            return img.resize(target_size, Image.Resampling.LANCZOS)
        else:
            # Different aspect ratios, crop to fit
            if original_ratio > target_ratio:
                # Original is wider, crop width
                new_width = int(original_height * target_ratio)
                left = (original_width - new_width) // 2
                img = img.crop((left, 0, left + new_width, original_height))
            else:
                # Original is taller, crop height
                new_height = int(original_width / target_ratio)
                top = (original_height - new_height) // 2
                img = img.crop((0, top, original_width, top + new_height))
            
            return img.resize(target_size, Image.Resampling.LANCZOS)
    
    def _enhance_image_quality(self, img: Image.Image) -> Image.Image:
        """Enhance image quality for better analysis"""
        enhanced_img = img.copy()
        
        # Enhance contrast
        contrast_enhancer = ImageEnhance.Contrast(enhanced_img)
        enhanced_img = contrast_enhancer.enhance(1.1)
        
        # Enhance sharpness slightly
        sharpness_enhancer = ImageEnhance.Sharpness(enhanced_img)
        enhanced_img = sharpness_enhancer.enhance(1.05)
        
        # Enhance color saturation slightly
        color_enhancer = ImageEnhance.Color(enhanced_img)
        enhanced_img = color_enhancer.enhance(1.05)
        
        return enhanced_img
    
    def _apply_image_filters(self, img: Image.Image, options: Dict) -> Image.Image:
        """Apply image filters based on options"""
        filtered_img = img.copy()
        
        # Apply slight blur reduction
        if options.get('reduce_blur', True):
            filtered_img = filtered_img.filter(ImageFilter.UnsharpMask(radius=1, percent=10, threshold=0))
        
        # Apply noise reduction
        if options.get('reduce_noise', True):
            filtered_img = filtered_img.filter(ImageFilter.MedianFilter(size=3))
        
        return filtered_img
    
    def _normalize_colors(self, img: Image.Image) -> Image.Image:
        """Normalize color distribution in image"""
        # Convert to numpy array for processing
        img_array = np.array(img)
        
        # Normalize each channel
        for channel in range(3):  # RGB channels
            channel_data = img_array[:, :, channel]
            
            # Calculate percentiles for robust normalization
            p2, p98 = np.percentile(channel_data, (2, 98))
            
            # Avoid division by zero
            if p98 > p2:
                channel_data = np.clip((channel_data - p2) / (p98 - p2) * 255, 0, 255)
                img_array[:, :, channel] = channel_data.astype(np.uint8)
        
        return Image.fromarray(img_array)
    
    def assess_image_quality(self, image_path: str) -> Dict:
        """
        Assess image quality for disease detection
        
        Args:
            image_path: Path to image file
            
        Returns:
            Quality assessment results
        """
        try:
            # Load image with OpenCV for analysis
            img_cv = cv2.imread(image_path)
            if img_cv is None:
                return {
                    'error': 'Could not load image for quality assessment',
                    'code': 'LOAD_ERROR'
                }
            
            # Convert to grayscale for some analyses
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
            
            # Assess blur (Laplacian variance)
            blur_score = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Assess brightness
            brightness = np.mean(gray)
            
            # Assess contrast
            contrast = gray.std()
            
            # Assess color distribution
            img_rgb = cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB)
            color_variance = np.var(img_rgb)
            
            # Assess image sharpness using edge detection
            edges = cv2.Canny(gray, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Calculate quality scores (0-1 scale)
            quality_scores = {
                'blur_score': min(blur_score / self.quality_thresholds['blur_threshold'], 1.0),
                'brightness_score': self._normalize_brightness(brightness),
                'contrast_score': min(contrast / 50, 1.0),  # Normalized to reasonable contrast range
                'color_variance': min(color_variance / 10000, 1.0),
                'edge_density': min(edge_density * 10, 1.0),
                'overall_quality': 0.0
            }
            
            # Calculate overall quality score
            weights = {
                'blur_score': 0.3,
                'brightness_score': 0.2,
                'contrast_score': 0.2,
                'color_variance': 0.15,
                'edge_density': 0.15
            }
            
            overall_quality = sum(
                quality_scores[metric] * weight 
                for metric, weight in weights.items()
            )
            quality_scores['overall_quality'] = overall_quality
            
            # Generate quality assessment
            assessment = self._generate_quality_assessment(quality_scores)
            
            return {
                'success': True,
                'scores': quality_scores,
                'assessment': assessment,
                'recommendations': self._generate_quality_recommendations(quality_scores)
            }
            
        except Exception as e:
            logging.error(f"Error assessing image quality: {e}")
            return {
                'error': 'Quality assessment failed',
                'code': 'ASSESSMENT_ERROR'
            }
    
    def _normalize_brightness(self, brightness: float) -> float:
        """Normalize brightness score to 0-1 range with optimal around 0.8"""
        optimal_brightness = 128  # Middle gray value
        max_deviation = 80
        
        deviation = abs(brightness - optimal_brightness)
        normalized = max(0, 1 - (deviation / max_deviation))
        
        return normalized
    
    def _generate_quality_assessment(self, scores: Dict) -> Dict:
        """Generate human-readable quality assessment"""
        overall = scores['overall_quality']
        
        if overall >= 0.8:
            level = 'Excellent'
            description = 'Image quality is excellent for disease detection'
        elif overall >= 0.6:
            level = 'Good'
            description = 'Image quality is good and suitable for analysis'
        elif overall >= 0.4:
            level = 'Fair'
            description = 'Image quality is fair but may affect accuracy'
        elif overall >= 0.2:
            level = 'Poor'
            description = 'Image quality is poor and may lead to inaccurate results'
        else:
            level = 'Very Poor'
            description = 'Image quality is very poor, consider retaking'
        
        return {
            'level': level,
            'score': round(overall * 100, 1),
            'description': description,
            'detailed_scores': {
                'blur': 'Sharp' if scores['blur_score'] > 0.6 else 'Blurry',
                'brightness': 'Good' if scores['brightness_score'] > 0.6 else 'Poor lighting',
                'contrast': 'Good' if scores['contrast_score'] > 0.5 else 'Low contrast',
                'detail': 'High detail' if scores['edge_density'] > 0.5 else 'Low detail'
            }
        }
    
    def _generate_quality_recommendations(self, scores: Dict) -> List[str]:
        """Generate recommendations for improving image quality"""
        recommendations = []
        
        if scores['blur_score'] < 0.5:
            recommendations.append("Hold camera steady or use tripod to reduce blur")
        
        if scores['brightness_score'] < 0.4:
            recommendations.append("Improve lighting conditions or adjust camera exposure")
        
        if scores['contrast_score'] < 0.3:
            recommendations.append("Increase contrast by adjusting lighting or camera settings")
        
        if scores['edge_density'] < 0.3:
            recommendations.append("Get closer to subject or focus on areas with visible symptoms")
        
        if scores['color_variance'] < 0.3:
            recommendations.append("Ensure good color representation with natural lighting")
        
        if not recommendations:
            recommendations.append("Image quality looks good for analysis")
        
        return recommendations
    
    def _get_applied_preprocessing(self, options: Dict) -> List[str]:
        """Get list of preprocessing steps that were applied"""
        applied = []
        
        if options.get('resize', True):
            applied.append('Resized to optimal dimensions')
        
        if options.get('enhance_quality', True):
            applied.append('Enhanced contrast and sharpness')
        
        if options.get('apply_filters', False):
            applied.append('Applied noise reduction filters')
        
        if options.get('normalize_colors', True):
            applied.append('Normalized color distribution')
        
        applied.append('Corrected image orientation')
        
        return applied
    
    def extract_plant_regions(self, image_path: str) -> Dict:
        """
        Extract potential plant regions from image using computer vision
        
        Args:
            image_path: Path to input image
            
        Returns:
            Dictionary with extracted regions information
        """
        try:
            img_cv = cv2.imread(image_path)
            if img_cv is None:
                return {
                    'success': False,
                    'error': 'Could not load image'
                }
            
            # Convert to different color spaces for plant detection
            hsv = cv2.cvtColor(img_cv, cv2.COLOR_BGR2HSV)
            lab = cv2.cvtColor(img_cv, cv2.COLOR_BGR2LAB)
            
            # Define green color ranges in HSV (for plant detection)
            lower_green1 = np.array([35, 40, 40])
            upper_green1 = np.array([85, 255, 255])
            
            lower_green2 = np.array([25, 40, 40])  # Yellow-green
            upper_green2 = np.array([35, 255, 255])
            
            # Create masks for green regions
            mask1 = cv2.inRange(hsv, lower_green1, upper_green1)
            mask2 = cv2.inRange(hsv, lower_green2, upper_green2)
            green_mask = cv2.bitwise_or(mask1, mask2)
            
            # Apply morphological operations to clean up the mask
            kernel = np.ones((5, 5), np.uint8)
            green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_CLOSE, kernel)
            green_mask = cv2.morphologyEx(green_mask, cv2.MORPH_OPEN, kernel)
            
            # Find contours of plant regions
            contours, _ = cv2.findContours(green_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by area
            min_area = img_cv.shape[0] * img_cv.shape[1] * 0.01  # At least 1% of image
            plant_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]
            
            # Calculate plant coverage
            total_plant_area = sum(cv2.contourArea(cnt) for cnt in plant_contours)
            total_image_area = img_cv.shape[0] * img_cv.shape[1]
            plant_coverage = total_plant_area / total_image_area
            
            # Get bounding rectangles for plant regions
            plant_regions = []
            for i, contour in enumerate(plant_contours[:5]):  # Limit to top 5 regions
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                
                plant_regions.append({
                    'id': i,
                    'bounding_box': {'x': x, 'y': y, 'width': w, 'height': h},
                    'area': area,
                    'area_percentage': (area / total_image_area) * 100
                })
            
            return {
                'success': True,
                'plant_coverage': round(plant_coverage * 100, 1),
                'num_regions': len(plant_regions),
                'regions': plant_regions,
                'has_sufficient_plant_content': plant_coverage > 0.1  # At least 10% plant content
            }
            
        except Exception as e:
            logging.error(f"Error extracting plant regions: {e}")
            return {
                'success': False,
                'error': 'Failed to extract plant regions'
            }
    
    def create_thumbnail(self, image_path: str, output_path: str, size: Tuple[int, int] = (150, 150)) -> Dict:
        """
        Create thumbnail image
        
        Args:
            image_path: Path to input image
            output_path: Path for output thumbnail
            size: Thumbnail size
            
        Returns:
            Operation result
        """
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnail maintaining aspect ratio
                img.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Create a square thumbnail with padding if needed
                thumbnail = Image.new('RGB', size, (255, 255, 255))
                
                # Center the image
                offset_x = (size[0] - img.size[0]) // 2
                offset_y = (size[1] - img.size[1]) // 2
                thumbnail.paste(img, (offset_x, offset_y))
                
                # Save thumbnail
                thumbnail.save(output_path, 'JPEG', quality=85)
                
                return {
                    'success': True,
                    'thumbnail_path': output_path,
                    'thumbnail_size': size,
                    'original_size': Image.open(image_path).size
                }
                
        except Exception as e:
            logging.error(f"Error creating thumbnail: {e}")
            return {
                'success': False,
                'error': 'Failed to create thumbnail'
            }
    
    def get_image_metadata(self, image_path: str) -> Dict:
        """
        Extract image metadata including EXIF data
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with image metadata
        """
        try:
            with Image.open(image_path) as img:
                # Basic image info
                metadata = {
                    'filename': os.path.basename(image_path),
                    'format': img.format,
                    'mode': img.mode,
                    'size': img.size,
                    'file_size': os.path.getsize(image_path)
                }
                
                # EXIF data
                exif_data = {}
                if hasattr(img, '_getexif'):
                    exif = img._getexif()
                    if exif:
                        for tag_id, value in exif.items():
                            tag = ExifTags.TAGS.get(tag_id, tag_id)
                            if isinstance(value, (int, float, str)):
                                exif_data[tag] = value
                
                metadata['exif'] = exif_data
                
                return {
                    'success': True,
                    'metadata': metadata
                }
                
        except Exception as e:
            logging.error(f"Error extracting metadata: {e}")
            return {
                'success': False,
                'error': 'Failed to extract metadata'
            }
    
    def health_check(self) -> bool:
        """Check if image processor is working correctly"""
        try:
            # Test basic image operations
            test_image = Image.new('RGB', (100, 100), (0, 255, 0))
            
            # Test resize
            resized = test_image.resize((50, 50))
            
            # Test enhancement
            enhancer = ImageEnhance.Contrast(test_image)
            enhanced = enhancer.enhance(1.1)
            
            # Test conversion
            gray = test_image.convert('L')
            
            return True
            
        except Exception as e:
            logging.error(f"Image processor health check failed: {e}")
            return False