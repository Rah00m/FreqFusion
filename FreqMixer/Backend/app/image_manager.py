"""
Image Manager Module

Handles image loading, storage, resizing, and Fourier Transform calculations.
Provides a comprehensive API for image processing operations.
"""

import cv2
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# try:
    # Try relative import (when used as package)
from .image_data import ImageData
from .image_utils import numpy_to_base64, apply_brightness_contrast, normalize_image, calculate_ft_components
# except ImportError:
    # # Fall back to direct import (when used as module)
    # from image_data import ImageData
    # from image_utils import numpy_to_base64, apply_brightness_contrast, normalize_image, calculate_ft_components


class ImageManager:
    """
    Core image management system for handling up to 4 images.
    
    Features:
    - Load and store images with automatic format conversion
    - Calculate common size across all loaded images
    - Resize images to uniform dimensions
    - Compute Fourier Transform components
    - Convert between numpy arrays and base64 for frontend display
    - Generate test images for development
    """
    
    # Constants
    MAX_IMAGES: int = 4
    MAX_IMAGE_DIMENSION: int = 5000
    
    def __init__(self) -> None:
        """Initialize the image manager with empty storage."""
        self.image_data: List[ImageData] = [ImageData(i) for i in range(self.MAX_IMAGES)]
        self.common_size: Optional[Tuple[int, int]] = None
        self._base64_cache: Dict[int, Optional[str]] = {i: None for i in range(self.MAX_IMAGES)}
    
    # ==================== Public API Methods ====================
    
    def load_image(self, image_id: int, file_bytes: bytes) -> Dict:
        """
        Load an image from byte data.
        
        Args:
            image_id: Image slot (0-3)
            file_bytes: Raw image bytes
            
        Returns:
            Status dict with success flag, size, and base64 data
        """
        if not self._validate_image_id(image_id):
            return {'success': False, 'error': 'Invalid image ID'}
        
        try:
            # Decode image from bytes
            nparr = np.frombuffer(file_bytes, np.uint8)
            image_np = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
            
            if image_np is None:
                raise ValueError("Cannot decode image")
            
            # Validate and convert to grayscale
            is_valid, message = self._validate_image_array(image_np)
            if not is_valid:
                raise ValueError(message)
            
            gray_image = self._convert_to_grayscale(image_np)
            
            # Store in ImageData structure
            self.image_data[image_id].path = f'image_{image_id}'
            self.image_data[image_id].original = gray_image.copy()
            self.image_data[image_id].current = gray_image.copy()
            self.image_data[image_id].loaded = True
            self.image_data[image_id].size = (gray_image.shape[1], gray_image.shape[0])
            
            # Update cache
            self._base64_cache[image_id] = numpy_to_base64(gray_image)
            
            # Update common size and auto-resize
            self._update_common_size()
            if self.common_size:
                self.resize_image_to_common(image_id)
            
            return {
                'success': True,
                'image_id': image_id,
                'size': {
                    'width': gray_image.shape[1],
                    'height': gray_image.shape[0]
                },
                'base64': self._base64_cache[image_id],
                'loaded': True
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_image(self, image_id: int) -> Optional[Dict]:
        """
        Get image data by ID (includes base64 for frontend).
        
        Args:
            image_id: Image slot (0-3)
            
        Returns:
            Image metadata dict or None if not loaded
        """
        if not self._validate_image_id(image_id) or not self.image_data[image_id].loaded:
            return None
        
        img_data = self.image_data[image_id]
        return {
            'id': image_id,
            'size': {'width': img_data.size[0], 'height': img_data.size[1]},
            'base64': self._base64_cache[image_id],
            'loaded': True
        }
    
    def get_image_numpy(self, image_id: int) -> Optional[np.ndarray]:
        """
        Get current image as numpy array.
        
        Args:
            image_id: Image slot (0-3)
            
        Returns:
            Numpy array or None if not loaded
        """
        if self._validate_image_id(image_id) and self.image_data[image_id].loaded:
            return self.image_data[image_id].current
        return None
    
    def get_original_image(self, image_id: int) -> Optional[np.ndarray]:
        """
        Get original (unmodified) image.
        
        Args:
            image_id: Image slot (0-3)
            
        Returns:
            Original numpy array or None if not loaded
        """
        if self._validate_image_id(image_id) and self.image_data[image_id].loaded:
            return self.image_data[image_id].original
        return None
    
    def get_all_images(self) -> Dict:
        """
        Get metadata for all images.
        
        Returns:
            Dict containing all image metadata, common size, and load count
        """
        images_list = []
        for img_id in range(self.MAX_IMAGES):
            if self.image_data[img_id].loaded:
                img_data = self.image_data[img_id]
                images_list.append({
                    'id': img_id,
                    'size': {'width': img_data.size[0], 'height': img_data.size[1]},
                    'base64': self._base64_cache[img_id],
                    'loaded': True
                })
            else:
                images_list.append({'id': img_id, 'loaded': False})
        
        return {
            'images': images_list,
            'common_size': self.common_size,
            'loaded_count': self.get_loaded_count()
        }
    
    def get_all_original_images(self) -> List[np.ndarray]:
        """
        Get all original images as numpy arrays.
        
        Returns:
            List of original numpy arrays
        """
        return [
            img_data.original 
            for img_data in self.image_data 
            if img_data.loaded and img_data.original is not None
        ]
    
    def get_image_info(self, image_id: int) -> Dict:
        """
        Get detailed info about a specific image.
        
        Args:
            image_id: Image slot (0-3)
            
        Returns:
            Image metadata dict
        """
        if not self._validate_image_id(image_id):
            return {}
        
        img_data = self.image_data[image_id]
        return {
            'id': img_data.id,
            'loaded': img_data.loaded,
            'size': img_data.size,
            'path': img_data.path
        }
    
    def update_image(self, image_id: int, image: np.ndarray) -> bool:
        """
        Update a specific image with new data.
        
        Args:
            image_id: Image slot (0-3)
            image: New numpy array
            
        Returns:
            True if successful, False otherwise
        """
        if not self._validate_image_id(image_id) or image is None:
            return False
        
        self.image_data[image_id].current = image.copy()
        self.image_data[image_id].size = (image.shape[1], image.shape[0])
        self._base64_cache[image_id] = numpy_to_base64(image)
        return True
    
    def delete_image(self, image_id: int) -> Dict:
        """
        Delete a specific image.
        
        Args:
            image_id: Image slot (0-3)
            
        Returns:
            Status dict with updated state
        """
        if not self._validate_image_id(image_id):
            return {'success': False, 'error': 'Invalid image ID'}
        
        self.image_data[image_id] = ImageData(image_id)
        self._base64_cache[image_id] = None
        self._update_common_size()
        
        return {
            'success': True,
            'deleted_id': image_id,
            'loaded_count': self.get_loaded_count(),
            'common_size': self.common_size
        }
    
    def delete_all_images(self) -> Dict:
        """
        Clear all images.
        
        Returns:
            Status dict
        """
        self.image_data = [ImageData(i) for i in range(self.MAX_IMAGES)]
        self._base64_cache = {i: None for i in range(self.MAX_IMAGES)}
        self.common_size = None
        
        return {
            'success': True,
            'message': 'All images cleared',
            'loaded_count': 0
        }
    
    def clear_image(self, image_id: int) -> None:
        """Clear a specific image."""
        self.delete_image(image_id)
    
    def clear_all(self) -> None:
        """Clear all images."""
        self.delete_all_images()
    
    def resize_image_to_common(self, image_id: int) -> Optional[Dict]:
        """
        Resize specific image to common size.
        
        Args:
            image_id: Image slot (0-3)
            
        Returns:
            Status dict or None if resize not possible
        """
        if not (self._validate_image_id(image_id) and self.image_data[image_id].loaded 
                and self.common_size and self.image_data[image_id].original is not None):
            return None
        
        original = self.image_data[image_id].original
        width, height = self.common_size
        
        resized = cv2.resize(original, (width, height), interpolation=cv2.INTER_AREA)
        self.image_data[image_id].current = resized
        self.image_data[image_id].size = self.common_size
        self._base64_cache[image_id] = numpy_to_base64(resized)
        
        return {
            'success': True,
            'image_id': image_id,
            'new_size': self.common_size,
            'base64': self._base64_cache[image_id]
        }
    
    def resize_all_to_common(self) -> Dict:
        """
        Resize all images to common size.
        
        Returns:
            Status dict
        """
        if self.common_size is None:
            return {'success': False, 'message': 'No common size calculated'}
        
        for img_id in range(self.MAX_IMAGES):
            if self.image_data[img_id].loaded:
                self.resize_image_to_common(img_id)
        
        return {
            'success': True,
            'common_size': self.common_size,
            'message': f'All images resized to {self.common_size[0]}x{self.common_size[1]}'
        }
    
    def get_loaded_count(self) -> int:
        """Get number of loaded images."""
        return sum(1 for img in self.image_data if img.loaded)
    
    def are_all_loaded(self) -> bool:
        """Check if all 4 images are loaded."""
        return self.get_loaded_count() == self.MAX_IMAGES
    
    def get_common_size(self) -> Optional[Tuple[int, int]]:
        """Get the common size across all loaded images."""
        return self.common_size
    
    def get_status(self) -> Dict:
        """
        Get current system status.
        
        Returns:
            Status dict with load counts and configuration
        """
        return {
            'loaded_count': self.get_loaded_count(),
            'common_size': self.common_size,
            'total_capacity': self.MAX_IMAGES,
            'images_loaded': [i for i in range(self.MAX_IMAGES) if self.image_data[i].loaded]
        }
    
    # ==================== Fourier Transform Methods ====================
    
    def calculate_ft_components(self, image_id: int) -> Dict:
        """
        Calculate Fourier Transform components for an image.
        
        Args:
            image_id: Image slot (0-3)
            
        Returns:
            Dict containing real, imaginary, magnitude, and phase components
        """
        image = self.get_image_numpy(image_id)
        if image is None:
            return {}
        
        return self._calculate_ft_components(image)
    
    def store_ft_components(self, image_id: int, ft_data: Dict) -> None:
        """
        Store Fourier Transform components for an image.
        
        Args:
            image_id: Image slot (0-3)
            ft_data: Dict with magnitude, phase, real, imaginary
        """
        if self._validate_image_id(image_id) and ft_data:
            img_data = self.image_data[image_id]
            img_data.ft_magnitude = ft_data.get('magnitude')
            img_data.ft_phase = ft_data.get('phase')
            img_data.ft_real = ft_data.get('real')
            img_data.ft_imaginary = ft_data.get('imaginary')
    
    def get_ft_components(self, image_id: int) -> Optional[Dict]:
        """
        Get stored Fourier Transform components.
        
        Args:
            image_id: Image slot (0-3)
            
        Returns:
            Dict of FT components or None
        """
        if not self._validate_image_id(image_id):
            return None
        
        img_data = self.image_data[image_id]
        if img_data.ft_magnitude is not None:
            return {
                'magnitude': img_data.ft_magnitude,
                'phase': img_data.ft_phase,
                'real': img_data.ft_real,
                'imaginary': img_data.ft_imaginary
            }
        return None
    
    # ==================== Image Processing Methods ====================
    
    def normalize_image(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize image to 0-255 range.
        
        Args:
            image: Input numpy array
            
        Returns:
            Normalized numpy array
        """
        return normalize_image(image)
    
    def apply_brightness_contrast(
        self, 
        image_id: int, 
        brightness: int = 0, 
        contrast: int = 0
    ) -> Optional[Dict]:
        """
        Apply brightness and contrast adjustments to an image.
        
        Args:
            image_id: Image slot (0-3)
            brightness: Brightness adjustment (-255 to 255)
            contrast: Contrast adjustment (-127 to 127)
            
        Returns:
            Status dict or None
        """
        image = self.get_image_numpy(image_id)
        if image is None:
            return None
        
        adjusted = self._apply_brightness_contrast(image.copy(), brightness, contrast)
        self.update_image(image_id, adjusted)
        
        return {'success': True, 'image_id': image_id}
    
    def get_image_statistics(self, image_id: int) -> Dict:
        """
        Calculate statistics for an image.
        
        Args:
            image_id: Image slot (0-3)
            
        Returns:
            Dict with mean, std, min, max, median, shape
        """
        image = self.get_image_numpy(image_id)
        if image is None:
            return {}
        
        return {
            'mean': float(np.mean(image)),
            'std': float(np.std(image)),
            'min': int(np.min(image)),
            'max': int(np.max(image)),
            'median': int(np.median(image)),
            'shape': image.shape
        }
    # ==================== Private Helper Methods ====================
    
    def _validate_image_id(self, image_id: int) -> bool:
        """Validate image ID is within range."""
        return 0 <= image_id < self.MAX_IMAGES
    
    def _validate_image_array(self, image: np.ndarray) -> Tuple[bool, str]:
        """
        Validate image array properties.
        
        Args:
            image: Numpy array to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if len(image.shape) not in [2, 3]:
            return False, "Invalid image dimensions"
        
        height, width = image.shape[:2]
        if width == 0 or height == 0:
            return False, "Image has zero dimensions"
        
        if width > self.MAX_IMAGE_DIMENSION or height > self.MAX_IMAGE_DIMENSION:
            return False, f"Image too large (max {self.MAX_IMAGE_DIMENSION}x{self.MAX_IMAGE_DIMENSION})"
        
        return True, "Valid image"
    
    def _convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """
        Convert image to grayscale.
        
        Args:
            image: Input numpy array (any format)
            
        Returns:
            Grayscale numpy array
        """
        if len(image.shape) == 2:
            return image  # Already grayscale
        
        if len(image.shape) == 3:
            if image.shape[2] == 3:
                return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            elif image.shape[2] == 4:
                return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        
        return image
    
    # Conversion helpers are provided by image_utils.numpy_to_base64/base64_to_numpy
    
    # Conversion helpers are provided by image_utils.numpy_to_base64/base64_to_numpy
    
    # Fourier Transform helpers are provided by image_utils.calculate_ft_components
    
    # Brightness/contrast helpers are provided by image_utils.apply_brightness_contrast
    
    def _update_common_size(self) -> None:
        """Calculate and update the common size across all loaded images."""
        loaded_images = [img for img in self.image_data if img.loaded]
        
        if not loaded_images:
            self.common_size = None
            return
        
        min_width = min(img.size[0] for img in loaded_images)
        min_height = min(img.size[1] for img in loaded_images)
        
        self.common_size = (min_width, min_height)