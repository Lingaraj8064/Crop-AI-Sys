"""
Crop Disease Detection System - File Handler Utilities
Utilities for handling file uploads, downloads, and management
"""

import os
import shutil
import hashlib
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from urllib.parse import urlparse
from PIL import Image
import tempfile

class FileHandler:
    """Utility class for file operations"""
    
    def __init__(self, upload_folder: str = 'static/uploads', max_file_size: int = 16 * 1024 * 1024):
        """
        Initialize file handler
        
        Args:
            upload_folder: Directory for uploaded files
            max_file_size: Maximum file size in bytes
        """
        self.upload_folder = upload_folder
        self.max_file_size = max_file_size
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'}
        self.allowed_mime_types = {
            'image/jpeg', 'image/jpg', 'image/png', 'image/bmp', 
            'image/gif', 'image/tiff', 'image/webp'
        }
        
        # Ensure upload directory exists
        os.makedirs(self.upload_folder, exist_ok=True)
    
    def save_uploaded_file(self, file: FileStorage, subfolder: str = None) -> Dict:
        """
        Save uploaded file to disk
        
        Args:
            file: FileStorage object from Flask
            subfolder: Optional subfolder within upload directory
            
        Returns:
            Dictionary with save operation results
        """
        try:
            # Validate file
            validation_result = self._validate_file(file)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': validation_result['error'],
                    'code': validation_result['code']
                }
            
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            file_extension = os.path.splitext(original_filename)[1].lower()
            unique_filename = self._generate_unique_filename(original_filename)
            
            # Determine save path
            if subfolder:
                save_dir = os.path.join(self.upload_folder, subfolder)
                os.makedirs(save_dir, exist_ok=True)
            else:
                save_dir = self.upload_folder
            
            file_path = os.path.join(save_dir, unique_filename)
            
            # Save file
            file.save(file_path)
            
            # Get file information
            file_size = os.path.getsize(file_path)
            file_hash = self._calculate_file_hash(file_path)
            
            # Validate saved image
            image_info = self._get_image_info(file_path)
            if not image_info['valid']:
                # Clean up invalid file
                os.remove(file_path)
                return {
                    'success': False,
                    'error': 'Invalid image file',
                    'code': 'INVALID_IMAGE'
                }
            
            return {
                'success': True,
                'filename': unique_filename,
                'file_path': file_path,
                'original_filename': original_filename,
                'file_size': file_size,
                'file_hash': file_hash,
                'file_type': file_extension,
                'image_info': image_info,
                'mime_type': file.mimetype
            }
            
        except Exception as e:
            logging.error(f"Error saving uploaded file: {e}")
            return {
                'success': False,
                'error': 'File save operation failed',
                'code': 'SAVE_ERROR'
            }
    
    def download_image_from_url(self, image_url: str, timeout: int = 30) -> Dict:
        """
        Download image from URL
        
        Args:
            image_url: URL of the image to download
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with download results
        """
        try:
            # Validate URL
            parsed_url = urlparse(image_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                return {
                    'success': False,
                    'error': 'Invalid URL format',
                    'code': 'INVALID_URL'
                }
            
            # Set headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            # Download file
            response = requests.get(image_url, headers=headers, timeout=timeout, stream=True)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if not any(mime_type in content_type for mime_type in self.allowed_mime_types):
                return {
                    'success': False,
                    'error': f'Unsupported content type: {content_type}',
                    'code': 'UNSUPPORTED_CONTENT_TYPE'
                }
            
            # Check file size
            content_length = response.headers.get('content-length')
            if content_length and int(content_length) > self.max_file_size:
                return {
                    'success': False,
                    'error': f'File too large: {content_length} bytes',
                    'code': 'FILE_TOO_LARGE'
                }
            
            # Generate filename from URL or use default
            url_path = parsed_url.path
            if url_path:
                original_filename = os.path.basename(url_path)
                if not original_filename or '.' not in original_filename:
                    original_filename = 'downloaded_image.jpg'
            else:
                original_filename = 'downloaded_image.jpg'
            
            # Ensure proper extension
            if not any(ext in original_filename.lower() for ext in self.allowed_extensions):
                original_filename += '.jpg'
            
            unique_filename = self._generate_unique_filename(original_filename)
            file_path = os.path.join(self.upload_folder, unique_filename)
            
            # Save downloaded content
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Validate downloaded image
            file_size = os.path.getsize(file_path)
            if file_size > self.max_file_size:
                os.remove(file_path)
                return {
                    'success': False,
                    'error': 'Downloaded file exceeds size limit',
                    'code': 'FILE_TOO_LARGE'
                }
            
            # Validate image
            image_info = self._get_image_info(file_path)
            if not image_info['valid']:
                os.remove(file_path)
                return {
                    'success': False,
                    'error': 'Downloaded file is not a valid image',
                    'code': 'INVALID_IMAGE'
                }
            
            file_hash = self._calculate_file_hash(file_path)
            
            return {
                'success': True,
                'filename': unique_filename,
                'file_path': file_path,
                'original_filename': original_filename,
                'file_size': file_size,
                'file_hash': file_hash,
                'source_url': image_url,
                'image_info': image_info,
                'download_size': file_size
            }
            
        except requests.RequestException as e:
            logging.error(f"Error downloading image from URL {image_url}: {e}")
            return {
                'success': False,
                'error': f'Failed to download image: {str(e)}',
                'code': 'DOWNLOAD_ERROR'
            }
        except Exception as e:
            logging.error(f"Unexpected error downloading image: {e}")
            return {
                'success': False,
                'error': 'Unexpected error during download',
                'code': 'UNEXPECTED_ERROR'
            }
    
    def delete_file(self, file_path: str) -> Dict:
        """
        Delete file from disk
        
        Args:
            file_path: Path to file to delete
            
        Returns:
            Dictionary with deletion results
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return {
                    'success': True,
                    'message': 'File deleted successfully',
                    'file_path': file_path
                }
            else:
                return {
                    'success': False,
                    'error': 'File not found',
                    'code': 'FILE_NOT_FOUND'
                }
                
        except Exception as e:
            logging.error(f"Error deleting file {file_path}: {e}")
            return {
                'success': False,
                'error': 'File deletion failed',
                'code': 'DELETE_ERROR'
            }
    
    def create_backup_copy(self, file_path: str, backup_folder: str = None) -> Dict:
        """
        Create backup copy of file
        
        Args:
            file_path: Original file path
            backup_folder: Optional backup directory
            
        Returns:
            Dictionary with backup results
        """
        try:
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': 'Source file not found',
                    'code': 'SOURCE_NOT_FOUND'
                }
            
            # Determine backup location
            if backup_folder:
                os.makedirs(backup_folder, exist_ok=True)
                backup_dir = backup_folder
            else:
                backup_dir = os.path.join(self.upload_folder, 'backups')
                os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup filename
            filename = os.path.basename(file_path)
            name, ext = os.path.splitext(filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{name}_backup_{timestamp}{ext}"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Copy file
            shutil.copy2(file_path, backup_path)
            
            return {
                'success': True,
                'backup_path': backup_path,
                'backup_filename': backup_filename,
                'original_path': file_path
            }
            
        except Exception as e:
            logging.error(f"Error creating backup of {file_path}: {e}")
            return {
                'success': False,
                'error': 'Backup creation failed',
                'code': 'BACKUP_ERROR'
            }
    
    def cleanup_old_files(self, days_old: int = 7) -> Dict:
        """
        Clean up files older than specified days
        
        Args:
            days_old: Remove files older than this many days
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            deleted_files = []
            total_size_freed = 0
            
            for root, dirs, files in os.walk(self.upload_folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        file_stat = os.stat(file_path)
                        if file_stat.st_mtime < cutoff_time:
                            file_size = file_stat.st_size
                            os.remove(file_path)
                            deleted_files.append({
                                'path': file_path,
                                'size': file_size,
                                'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat()
                            })
                            total_size_freed += file_size
                            
                    except (OSError, IOError) as file_error:
                        logging.warning(f"Could not process file {file_path}: {file_error}")
                        continue
            
            return {
                'success': True,
                'deleted_count': len(deleted_files),
                'deleted_files': deleted_files,
                'total_size_freed': total_size_freed,
                'days_old_threshold': days_old
            }
            
        except Exception as e:
            logging.error(f"Error during file cleanup: {e}")
            return {
                'success': False,
                'error': 'File cleanup failed',
                'code': 'CLEANUP_ERROR'
            }
    
    def get_directory_info(self, directory: str = None) -> Dict:
        """
        Get information about directory contents
        
        Args:
            directory: Directory to analyze (defaults to upload folder)
            
        Returns:
            Dictionary with directory information
        """
        try:
            target_dir = directory or self.upload_folder
            
            if not os.path.exists(target_dir):
                return {
                    'success': False,
                    'error': 'Directory not found',
                    'code': 'DIRECTORY_NOT_FOUND'
                }
            
            total_files = 0
            total_size = 0
            file_types = {}
            oldest_file = None
            newest_file = None
            
            for root, dirs, files in os.walk(target_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        file_stat = os.stat(file_path)
                        file_size = file_stat.st_size
                        file_mtime = file_stat.st_mtime
                        
                        total_files += 1
                        total_size += file_size
                        
                        # Track file extensions
                        _, ext = os.path.splitext(file)
                        ext = ext.lower()
                        file_types[ext] = file_types.get(ext, 0) + 1
                        
                        # Track oldest and newest files
                        if oldest_file is None or file_mtime < oldest_file['mtime']:
                            oldest_file = {
                                'path': file_path,
                                'mtime': file_mtime,
                                'date': datetime.fromtimestamp(file_mtime).isoformat()
                            }
                        
                        if newest_file is None or file_mtime > newest_file['mtime']:
                            newest_file = {
                                'path': file_path,
                                'mtime': file_mtime,
                                'date': datetime.fromtimestamp(file_mtime).isoformat()
                            }
                            
                    except (OSError, IOError):
                        continue
            
            return {
                'success': True,
                'directory': target_dir,
                'total_files': total_files,
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'file_types': file_types,
                'oldest_file': oldest_file,
                'newest_file': newest_file,
                'average_file_size': total_size / total_files if total_files > 0 else 0
            }
            
        except Exception as e:
            logging.error(f"Error analyzing directory {target_dir}: {e}")
            return {
                'success': False,
                'error': 'Directory analysis failed',
                'code': 'ANALYSIS_ERROR'
            }
    
    def _validate_file(self, file: FileStorage) -> Dict:
        """Validate uploaded file"""
        # Check if file exists
        if not file or file.filename == '':
            return {
                'valid': False,
                'error': 'No file provided',
                'code': 'NO_FILE'
            }
        
        # Check file extension
        filename = secure_filename(file.filename)
        file_extension = os.path.splitext(filename)[1].lower()
        
        if file_extension not in self.allowed_extensions:
            return {
                'valid': False,
                'error': f'Unsupported file extension: {file_extension}',
                'code': 'UNSUPPORTED_EXTENSION'
            }
        
        # Check MIME type
        if file.mimetype and file.mimetype not in self.allowed_mime_types:
            return {
                'valid': False,
                'error': f'Unsupported MIME type: {file.mimetype}',
                'code': 'UNSUPPORTED_MIME_TYPE'
            }
        
        # Check file size (if available)
        if hasattr(file, 'content_length') and file.content_length:
            if file.content_length > self.max_file_size:
                return {
                    'valid': False,
                    'error': f'File too large: {file.content_length} bytes',
                    'code': 'FILE_TOO_LARGE'
                }
        
        return {'valid': True}
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename with timestamp"""
        name, ext = os.path.splitext(secure_filename(original_filename))
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # microseconds to milliseconds
        return f"{name}_{timestamp}{ext}"
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logging.error(f"Error calculating file hash: {e}")
            return ""
    
    def _get_image_info(self, file_path: str) -> Dict:
        """Get image information and validate"""
        try:
            with Image.open(file_path) as img:
                # Verify the image
                img.verify()
                
                # Reopen for getting info (verify closes the file)
                with Image.open(file_path) as img_info:
                    return {
                        'valid': True,
                        'width': img_info.width,
                        'height': img_info.height,
                        'mode': img_info.mode,
                        'format': img_info.format,
                        'has_transparency': img_info.mode in ('RGBA', 'LA', 'P')
                    }
                    
        except Exception as e:
            logging.error(f"Error validating image {file_path}: {e}")
            return {
                'valid': False,
                'error': str(e)
            }
    
    def move_file(self, source_path: str, destination_path: str) -> Dict:
        """Move file from source to destination"""
        try:
            if not os.path.exists(source_path):
                return {
                    'success': False,
                    'error': 'Source file not found',
                    'code': 'SOURCE_NOT_FOUND'
                }
            
            # Ensure destination directory exists
            dest_dir = os.path.dirname(destination_path)
            os.makedirs(dest_dir, exist_ok=True)
            
            # Move file
            shutil.move(source_path, destination_path)
            
            return {
                'success': True,
                'source_path': source_path,
                'destination_path': destination_path
            }
            
        except Exception as e:
            logging.error(f"Error moving file from {source_path} to {destination_path}: {e}")
            return {
                'success': False,
                'error': 'File move operation failed',
                'code': 'MOVE_ERROR'
            }
    
    def get_file_info(self, file_path: str) -> Dict:
        """Get detailed information about a file"""
        try:
            if not os.path.exists(file_path):
                return {
                    'success': False,
                    'error': 'File not found',
                    'code': 'FILE_NOT_FOUND'
                }
            
            stat = os.stat(file_path)
            
            file_info = {
                'success': True,
                'path': file_path,
                'filename': os.path.basename(file_path),
                'size': stat.st_size,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'accessed': datetime.fromtimestamp(stat.st_atime).isoformat(),
                'file_hash': self._calculate_file_hash(file_path)
            }
            
            # Add image-specific info if it's an image
            if any(ext in file_path.lower() for ext in self.allowed_extensions):
                image_info = self._get_image_info(file_path)
                file_info['image_info'] = image_info
            
            return file_info
            
        except Exception as e:
            logging.error(f"Error getting file info for {file_path}: {e}")
            return {
                'success': False,
                'error': 'Failed to get file information',
                'code': 'INFO_ERROR'
            }