"""
Utility module providing image utilities and custom JSON encoding.

Integrates with image_utils.py for core image processing functions.
Also provides JsonEncoder for numpy array serialization in FastAPI responses.
"""

import json
from typing import Dict, Optional, Tuple, List
import numpy as np
import cv2

# Re-export core image utilities
# try:
from .image_utils import (
        calculate_ft_components,
        normalize_image,
        apply_brightness_contrast,
        numpy_to_base64,
        base64_to_numpy,
    )
# except ImportError:
#     from image_utils import (
#         calculate_ft_components,
#         normalize_image,
#         apply_brightness_contrast,
#         numpy_to_base64,
#         base64_to_numpy,
#     )


class ImageUtils:
    """
    Utility functions for image processing.
    
    This class provides static wrappers around the image_utils module functions
    for backward compatibility. New code should use image_utils functions directly.
    """
    
    @staticmethod
    def calculate_ft_components(image: np.ndarray) -> dict:
        """Calculate Fourier Transform components"""
        return calculate_ft_components(image)
    
    @staticmethod
    def normalize_image(image: np.ndarray) -> np.ndarray:
        """Normalize image to 0-255 range"""
        return normalize_image(image)
    
    @staticmethod
    def apply_brightness_contrast(image: np.ndarray, brightness: int = 0, contrast: int = 0) -> np.ndarray:
        """Apply brightness and contrast adjustments"""
        return apply_brightness_contrast(image, brightness, contrast)
    
    @staticmethod
    def numpy_to_base64(image_np: np.ndarray) -> str:
        """Convert numpy array to base64 string"""
        return numpy_to_base64(image_np)
    
    @staticmethod
    def base64_to_numpy(base64_str: str) -> Optional[np.ndarray]:
        """Convert base64 string to numpy array"""
        return base64_to_numpy(base64_str)
    
    @staticmethod
    def calculate_minimum_size(images: List[np.ndarray]) -> Optional[Tuple[int, int]]:
        """Calculate minimum size that fits all images"""
        if not images:
            return None
        
        widths = []
        heights = []
        
        for img in images:
            if img is not None:
                heights.append(img.shape[0])
                widths.append(img.shape[1])
        
        if not widths or not heights:
            return None
        
        return (min(widths), min(heights))
    
    @staticmethod
    def resize_to_common(images: List[np.ndarray], target_size: Tuple[int, int]) -> List[np.ndarray]:
        """Resize list of images to common size"""
        if not target_size:
            return images
        
        resized_images = []
        width, height = target_size
        
        for img in images:
            if img is not None:
                resized = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)
                resized_images.append(resized)
            else:
                resized_images.append(None)
        
        return resized_images
    
    @staticmethod
    def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
        """Convert image to grayscale"""
        if image is None:
            return None
        
        if len(image.shape) == 2:  # Already grayscale
            return image
        
        if len(image.shape) == 3:
            if image.shape[2] == 3:  # RGB
                return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            elif image.shape[2] == 4:  # RGBA
                return cv2.cvtColor(image, cv2.COLOR_BGRA2GRAY)
        
        return image
    
    @staticmethod
    def create_sample_image(width: int, height: int, pattern_type: str = 'gradient') -> np.ndarray:
        """Create a sample test image"""
        
        if pattern_type == 'gradient':
            # Horizontal gradient
            image = np.zeros((height, width), dtype=np.uint8)
            for y in range(height):
                image[y, :] = np.linspace(0, 255, width, dtype=np.uint8)
        
        elif pattern_type == 'vertical_gradient':
            # Vertical gradient
            image = np.zeros((height, width), dtype=np.uint8)
            for x in range(width):
                image[:, x] = np.linspace(0, 255, height, dtype=np.uint8)
        
        elif pattern_type == 'checkerboard':
            # Checkerboard pattern
            image = np.zeros((height, width), dtype=np.uint8)
            square_size = 30
            for y in range(0, height, square_size):
                for x in range(0, width, square_size):
                    if (x//square_size + y//square_size) % 2 == 0:
                        image[y:y+square_size, x:x+square_size] = 200
        
        elif pattern_type == 'circles':
            # Concentric circles
            image = np.zeros((height, width), dtype=np.uint8)
            center_x, center_y = width // 2, height // 2
            max_radius = min(center_x, center_y)
            
            for r in range(10, max_radius, 40):
                cv2.circle(image, (center_x, center_y), r, 150, 5)
        
        else:
            # Solid gray
            image = np.full((height, width), 128, dtype=np.uint8)
        
        return image
    
    @staticmethod
    def calculate_image_statistics(image: np.ndarray) -> Dict:
        """Calculate basic statistics of an image"""
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
    
    @staticmethod
    def validate_image_file(file_bytes: bytes) -> Tuple[bool, str]:
        """Validate if bytes represent a valid image"""
        try:
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
            
            if img is None:
                return False, "Cannot decode image"
            
            # Check dimensions
            if len(img.shape) not in [2, 3]:
                return False, "Invalid image dimensions"
            
            # Check size
            height, width = img.shape[:2]
            if width == 0 or height == 0:
                return False, "Image has zero dimensions"
            
            if width > 5000 or height > 5000:
                return False, "Image too large (max 5000x5000)"
            
            return True, "Valid image"
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"


class JsonEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy arrays and standard types."""
    
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        return super().default(obj)