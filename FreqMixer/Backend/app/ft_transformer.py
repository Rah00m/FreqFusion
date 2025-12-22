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
    """Dual-path storage with clear separation between operations and visualization.
    
    ARCHITECTURE:
    - ft_original: Unshifted FT for mathematical operations (mixing, filtering)
    - ft_shifted: Shifted FT for visualization ONLY (low frequencies in center)
    - Raw components: From ft_original (for operations)
    - Display components: From ft_shifted (for user display)
    
    CRITICAL: Never use ft_shifted for mathematical operations!
    """
    # FOR OPERATIONS (mathematical correctness)
    ft_original: np.ndarray           # Unshifted - for mixing operations
    magnitude_raw: np.ndarray         # From ft_original
    phase_raw: np.ndarray             # From ft_original
    real_raw: np.ndarray              # From ft_original
    imaginary_raw: np.ndarray         # From ft_original
    
    # FOR VISUALIZATION ONLY (user display)
    ft_shifted: np.ndarray            # Shifted - for display only
    magnitude_display: np.ndarray     # From ft_shifted (log-scaled)
    phase_display: np.ndarray         # From ft_shifted (normalized)
    real_display: np.ndarray          # From ft_shifted (normalized)
    imaginary_display: np.ndarray     # From ft_shifted (normalized)

    def to_dict(self) -> Dict:
        return {
            "ft_shape": self.ft_original.shape,
            "dtype": str(self.ft_original.dtype),
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
        """Get raw component from ft_original (for operations)"""
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

        # Dual-path calculation
        ft_original = np.fft.fft2(image_gray)  # For operations
        ft_shifted = np.fft.fftshift(ft_original)  # For display only

        comps = self._extract_components(ft_original, ft_shifted)

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

    def _extract_components(self, ft_original: np.ndarray, ft_shifted: np.ndarray) -> FTComponents:
        """Extract components from dual paths.
        
        RAW components: From ft_original (unshifted) for mathematical operations
        DISPLAY components: From ft_shifted (centered) for visualization
        
        CRITICAL: Raw components are for operations, display for visualization only!
        """
        # RAW components from ft_original (for mixing operations)
        magnitude_raw = np.abs(ft_original)
        phase_raw = np.angle(ft_original)
        real_raw = ft_original.real
        imaginary_raw = ft_original.imag

        # DISPLAY components from ft_shifted (for visualization)
        magnitude_shifted = np.abs(ft_shifted)
        phase_shifted = np.angle(ft_shifted)
        real_shifted = ft_shifted.real
        imaginary_shifted = ft_shifted.imag
        
        # Normalize display components for visualization
        magnitude_display = self._normalize_magnitude(magnitude_shifted)
        phase_display = self._normalize_phase(phase_shifted)
        real_display = self._normalize_real_imag(real_shifted)
        imag_display = self._normalize_real_imag(imaginary_shifted)

        return FTComponents(
            ft_original=ft_original,
            magnitude_raw=magnitude_raw,
            phase_raw=phase_raw,
            real_raw=real_raw,
            imaginary_raw=imaginary_raw,
            ft_shifted=ft_shifted,
            magnitude_display=magnitude_display,
            phase_display=phase_display,
            real_display=real_display,
            imaginary_display=imag_display,
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

    def convert_rectangle_coordinates(self, rect: Dict, image_shape: Tuple[int, int]) -> Dict:
        """Convert rectangle coordinates from shifted domain (user view) to original domain (operations).
        
        User draws on: ft_shifted (low frequencies in center)
        We operate on: ft_original (low frequencies in corners)
        
        Conversion formula:
        x_original = (x_shifted - width/2) % width
        y_original = (y_shifted - height/2) % height
        """
        h, w = image_shape
        
        # Coordinates from user (drawn on ft_shifted)
        x_shifted = rect["x"]
        y_shifted = rect["y"]
        
        # Convert to ft_original domain
        x_original = (x_shifted - w // 2) % w
        y_original = (y_shifted - h // 2) % h
        
        return {
            "x": x_original,
            "y": y_original,
            "width": rect["width"],
            "height": rect["height"],
            "type": rect["type"]
        }

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

    def apply_region_mask(self, ft_original: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Apply a boolean mask to an FT array; expects matching shapes."""
        if ft_original.shape != mask.shape:
            raise ValueError("Region mask shape does not match FT shape")
        return ft_original * mask

    def mix_components(
        self,
        components_list: List[FTComponents],
        weights: List[List[float]],
        rectangles: List[Optional[Dict]],
        component_mode: str = "magnitude_phase",
        preserve_energy: bool = False,
    ) -> Dict:
        """Mix FT components using ft_original with coordinate conversion.
        
        CRITICAL: 
        - User rectangles are in ft_shifted domain (centered)
        - Convert to ft_original domain before applying masks
        - All operations use ft_original for mathematical correctness
        """
        if len(components_list) != len(weights):
            raise ValueError(f"Components count {len(components_list)} != weights count {len(weights)}")
        if len(rectangles) != len(weights):
            raise ValueError(f"Rectangles count {len(rectangles)} != weights count {len(weights)}")
        if component_mode not in ("magnitude_phase", "real_imaginary"):
            raise ValueError(f"Invalid component_mode: {component_mode}")

        shapes = {comp.ft_original.shape for comp in components_list}
        if len(shapes) != 1:
            raise ValueError("FT component shapes differ across images")
        target_shape = components_list[0].ft_original.shape

        def as_float_pair(pair: List[float]) -> Tuple[float, float]:
            if len(pair) != 2:
                raise ValueError("Each weight entry must have exactly 2 values")
            a = float(pair[0]) if np.isfinite(pair[0]) else 0.0
            b = float(pair[1]) if np.isfinite(pair[1]) else 0.0
            return a, b

        mixed_ft = np.zeros(target_shape, dtype=np.complex128)

        for comp, pair, rect in zip(components_list, weights, rectangles):
            w1, w2 = as_float_pair(pair)

            if component_mode == "magnitude_phase":
                # ⭐ CRITICAL: Use raw components from ft_original
                magnitude = comp.magnitude_raw * w1
                phase = comp.phase_raw * w2
                ft_component = magnitude * np.exp(1j * phase)
            else:  # real_imaginary
                real_scaled = comp.real_raw * w1
                imag_scaled = comp.imaginary_raw * w2
                ft_component = real_scaled + 1j * imag_scaled

            if rect is not None:
                # ⭐ Convert rectangle from shifted domain to original domain
                rect_converted = self.convert_rectangle_coordinates(rect, target_shape)
                mask = self.create_rect_region_mask(
                    target_shape,
                    int(rect_converted["x"]),
                    int(rect_converted["y"]),
                    int(rect_converted["width"]),
                    int(rect_converted["height"]),
                    rect_converted["type"],
                )
                ft_component = ft_component * mask.astype(np.complex128)

            mixed_ft += ft_component

        raw_image, display_image = self.inverse_ft(mixed_ft, preserve_energy)
        raw_image = np.nan_to_num(raw_image, nan=0.0, posinf=255.0, neginf=0.0)
        display_image = np.nan_to_num(display_image, nan=0.0, posinf=255.0, neginf=0.0)

        return {"display": display_image, "raw": raw_image}

    def inverse_ft(self, ft_unshifted: np.ndarray, preserve_energy: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """Inverse FFT - receives unshifted FT from mix_components.
        
        Args:
            ft_unshifted: Complex FT array (from ft_original domain, not shifted)
            preserve_energy: If True, don't scale raw output
            
        Returns:
            Tuple of (raw_float_image, display_uint8_image)
        """
        # ft_unshifted is already unshifted from mix_components
        image_reconstructed = np.fft.ifft2(ft_unshifted)
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
            comp.ft_original.nbytes
            + comp.ft_shifted.nbytes
            + comp.magnitude_raw.nbytes
            + comp.phase_raw.nbytes
            + comp.real_raw.nbytes
            + comp.imaginary_raw.nbytes
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