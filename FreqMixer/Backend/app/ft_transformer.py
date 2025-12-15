"""
Fourier Transformer Module

Provides FourierTransformer to compute 2D FFT components (magnitude, phase, real, imaginary),
region masks, mixing, reconstruction, and caching for image mixing tasks.
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from .image_utils import (
        numpy_to_base64,
    )

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FTComponents:
    """Container for Fourier Transform components."""
    ft_shifted: np.ndarray
    magnitude_display: np.ndarray
    phase_display: np.ndarray
    real_display: np.ndarray
    imaginary_display: np.ndarray
    magnitude_raw: np.ndarray
    phase_raw: np.ndarray
    real_raw: np.ndarray
    imaginary_raw: np.ndarray

    def to_dict(self) -> Dict:
        return {
            "ft_shape": self.ft_shifted.shape,
            "dtype": str(self.ft_shifted.dtype),
            "magnitude_shape": self.magnitude_display.shape,
            "phase_shape": self.phase_display.shape,
            "real_shape": self.real_display.shape,
            "imaginary_shape": self.imaginary_display.shape,
        }

    def get_display_component(self, name: str) -> np.ndarray:
        mapping = {
            "magnitude": self.magnitude_display,
            "phase": self.phase_display,
            "real": self.real_display,
            "imaginary": self.imaginary_display,
        }
        key = name.lower()
        if key not in mapping:
            raise ValueError(f"Invalid component: {name}")
        return mapping[key]

    def get_raw_component(self, name: str) -> np.ndarray:
        mapping = {
            "magnitude": self.magnitude_raw,
            "phase": self.phase_raw,
            "real": self.real_raw,
            "imaginary": self.imaginary_raw,
        }
        key = name.lower()
        if key not in mapping:
            raise ValueError(f"Invalid component: {name}")
        return mapping[key]


class FourierTransformer:
    """Comprehensive Fourier Transform helper for 2D images."""

    def __init__(self, use_float32: bool = True) -> None:
        self.use_float32 = use_float32
        self.cache: Dict[str, FTComponents] = {}
        logger.info("FourierTransformer initialized")

    def calculate_ft(self, image: np.ndarray, image_id: Optional[str] = None) -> FTComponents:
        if image is None:
            raise ValueError("Input image cannot be None")
        if image.ndim not in (2, 3):
            raise ValueError(f"Invalid image dimensions: {image.shape}")

        if image_id and image_id in self.cache:
            return self.cache[image_id]

        image_gray = self._ensure_grayscale(image)
        image_gray = image_gray.astype(np.float32 if self.use_float32 else np.float64)

        ft_original = np.fft.fft2(image_gray)
        ft_shifted = np.fft.fftshift(ft_original)

        comps = self._extract_components(ft_shifted)

        if image_id:
            self.cache[image_id] = comps
        return comps

    def _ensure_grayscale(self, image: np.ndarray) -> np.ndarray:
        if image.ndim == 3:
            if image.shape[2] == 3:
                return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            if image.shape[2] == 4:
                rgb = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
                return cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            if image.shape[2] == 1:
                return image.squeeze()
        return image

    def _extract_components(self, ft_shifted: np.ndarray) -> FTComponents:
        magnitude_raw = np.abs(ft_shifted)
        phase_raw = np.angle(ft_shifted)
        real_raw = ft_shifted.real
        imaginary_raw = ft_shifted.imag

        magnitude_display = self._normalize_magnitude(magnitude_raw)
        phase_display = self._normalize_phase(phase_raw)
        real_display = self._normalize_real_imag(real_raw)
        imag_display = self._normalize_real_imag(imaginary_raw)

        return FTComponents(
            ft_shifted=ft_shifted,
            magnitude_display=magnitude_display,
            phase_display=phase_display,
            real_display=real_display,
            imaginary_display=imag_display,
            magnitude_raw=magnitude_raw,
            phase_raw=phase_raw,
            real_raw=real_raw,
            imaginary_raw=imaginary_raw,
        )

    def _normalize_magnitude(self, magnitude: np.ndarray) -> np.ndarray:
        magnitude_safe = np.maximum(magnitude, 1e-10)
        magnitude_log = np.log1p(magnitude_safe)
        magnitude_norm = cv2.normalize(magnitude_log, None, 0, 255, cv2.NORM_MINMAX)
        return magnitude_norm.astype(np.uint8)

    def _normalize_phase(self, phase: np.ndarray) -> np.ndarray:
        phase_shifted = phase + np.pi
        phase_normalized = (phase_shifted / (2 * np.pi)) * 255
        return np.clip(phase_normalized, 0, 255).astype(np.uint8)

    def _normalize_real_imag(self, component: np.ndarray) -> np.ndarray:
        component_norm = cv2.normalize(component, None, 0, 255, cv2.NORM_MINMAX)
        return component_norm.astype(np.uint8)

    def create_rect_region_mask(
        self,
        shape: Tuple[int, int],
        x: int,
        y: int,
        width: int,
        height: int,
        region_type: str = "inner",
    ) -> np.ndarray:
        """Create a boolean mask for a rectangular region (inner or outer).
        
        Args:
            shape: (height, width) of FT array
            x, y: top-left corner of rectangle
            width, height: dimensions of rectangle
            region_type: 'inner' = inside rectangle, 'outer' = outside rectangle
        
        Returns:
            Boolean mask matching shape
        """
        h, w = shape
        mask = np.zeros((h, w), dtype=bool)
        
        # Clip rectangle bounds to image
        x1 = max(0, x)
        y1 = max(0, y)
        x2 = min(w, x + width)
        y2 = min(h, y + height)
        
        # Mark rectangle region
        mask[y1:y2, x1:x2] = True
        
        # Return either inner or outer region
        return mask if region_type == "inner" else ~mask
    
    def create_region_mask(
        self,
        shape: Tuple[int, int],
        region_percentage: float,
        region_type: str = "inner",
    ) -> np.ndarray:
        """Deprecated: kept for backward compat. Creates circular mask."""
        if region_percentage >= 100:
            return np.ones(shape, dtype=bool)
        h, w = shape
        cy, cx = h // 2, w // 2
        radius = int(min(h, w) * region_percentage / 100 / 2)
        y, x = np.ogrid[:h, :w]
        dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
        if region_type == "inner":
            mask = dist <= radius
        else:
            mask = dist > radius
        return mask

    def apply_region_mask(self, ft_shifted: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Apply a boolean mask to an FT array; expects matching shapes."""
        if ft_shifted.shape != mask.shape:
            raise ValueError("Region mask shape does not match FT shape")
        return ft_shifted * mask

    def mix_components(
        self,
        components_list: List[FTComponents],
        weights: List[float],
        rectangles: List[Optional[Dict]],
        component_mode: str = 'magnitude_phase',
        preserve_energy: bool = False,
    ) -> Dict:
        """Mix FT components with per-image rectangular masks.
        
        Args:
            components_list: List of FTComponents (one per image)
            weights: Weight for each image (will be normalized)
            rectangles: List of rectangle dicts {x, y, width, height, type} per image
                       Use None for full region (no mask)
            component_mode: 'magnitude_phase' or 'real_imaginary'
            preserve_energy: If True, preserve spectral energy
            
        Returns:
            Dict with 'display' and 'raw' numpy arrays
        """
        # Validate inputs
        if len(components_list) != len(weights):
            raise ValueError(f"Components count {len(components_list)} != weights count {len(weights)}")
        
        if len(rectangles) != len(weights):
            raise ValueError(f"Rectangles count {len(rectangles)} != weights count {len(weights)}")
        
        if component_mode not in ('magnitude_phase', 'real_imaginary'):
            raise ValueError(f"Invalid component_mode: {component_mode}")
        
        # Check all FT components have same shape
        shapes = {comp.ft_shifted.shape for comp in components_list}
        if len(shapes) != 1:
            raise ValueError("FT component shapes differ across images")
        
        target_shape = components_list[0].ft_shifted.shape
        
        # Normalize weights
        weight_sum = sum(weights)
        if weight_sum == 0:
            raise ValueError("Weights sum to zero")
        normalized_weights = [w / weight_sum for w in weights]
        
        # Initialize mixed FT array
        mixed_ft = np.zeros(target_shape, dtype=np.complex128)
        
        # Process each image with its rectangle
        for idx, (comp, weight, rect) in enumerate(zip(components_list, normalized_weights, rectangles)):
            # Extract frequency components based on mode
            if component_mode == 'magnitude_phase':
                magnitude = comp.magnitude_raw
                phase = comp.phase_raw
                ft_component = magnitude * np.exp(1j * phase)
            else:  # real_imaginary
                ft_component = comp.real_raw + 1j * comp.imaginary_raw
            
            # Create and apply per-image mask if rectangle provided
            if rect is not None:
                mask = self.create_rect_region_mask(
                    target_shape,
                    int(rect.get('x', 0)),
                    int(rect.get('y', 0)),
                    int(rect.get('width', 0)),
                    int(rect.get('height', 0)),
                    rect.get('type', 'inner'),
                )
                ft_component = ft_component * mask.astype(np.complex128)
            
            # Accumulate weighted contribution
            mixed_ft += weight * ft_component
        
        # Perform inverse FFT
        raw_image, display_image = self.inverse_ft(mixed_ft, preserve_energy)
        
        return {
            'display': display_image,
            'raw': raw_image,
        }


    def inverse_ft(self, ft_shifted: np.ndarray, preserve_energy: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """Inverse FFT with optional energy preservation.

        Returns a tuple of (raw_float_image, display_uint8_image). When preserve_energy is
        True, no min-max scaling is applied to the raw output; display output remains
        normalized for visualization only.
        """
        ft_original = np.fft.ifftshift(ft_shifted)
        image_reconstructed = np.fft.ifft2(ft_original)
        image_real = np.real(image_reconstructed)

        raw_image = image_real 
        display_image = self._to_display(image_real)
        return raw_image, display_image

    def _to_display(self, image: np.ndarray) -> np.ndarray:
        """Normalize an arbitrary float image to uint8 for display only."""
        norm = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
        return np.clip(norm, 0, 255).astype(np.uint8)

    def clear_cache(self, image_id: Optional[str] = None) -> None:
        if image_id:
            self.cache.pop(image_id, None)
        else:
            self.cache.clear()

    def get_cache_info(self) -> Dict:
        total_memory = sum(
            comp.ft_shifted.nbytes
            + comp.magnitude_display.nbytes
            + comp.phase_display.nbytes
            + comp.real_display.nbytes
            + comp.imaginary_display.nbytes
            for comp in self.cache.values()
        )
        return {
            "cache_size": len(self.cache),
            "cached_ids": list(self.cache.keys()),
            "memory_bytes": total_memory,
            "memory_mb": total_memory / (1024 * 1024),
        }
