"""
Stateless image utility functions.

Provides helpers for array/base64 conversion, normalization, and brightness/contrast.
All Fourier Transform logic lives in ft_transformer.py.
"""

import base64
from io import BytesIO
from typing import Optional

import cv2
import numpy as np
from PIL import Image


def numpy_to_base64(image: np.ndarray) -> str:
    """Convert a numpy image array to a PNG base64 string."""
    if image is None:
        return ""
    if image.dtype != np.uint8:
        image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    pil_img = Image.fromarray(image)
    buffered = BytesIO()
    pil_img.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def base64_to_numpy(base64_str: str) -> Optional[np.ndarray]:
    """Convert a PNG base64 string to a grayscale numpy array."""
    if not base64_str:
        return None
    try:
        img_bytes = base64.b64decode(base64_str)
        nparr = np.frombuffer(img_bytes, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
    except Exception:
        return None


def normalize_image(image: np.ndarray) -> np.ndarray:
    """Normalize image values to 0-255 uint8 range."""
    if image is None or image.size == 0:
        return image
    if np.all(image == image.flat[0]):
        return np.zeros_like(image, dtype=np.uint8)
    min_val = np.min(image)
    max_val = np.max(image)
    if max_val == min_val:
        return np.zeros_like(image, dtype=np.uint8)
    normalized = (image - min_val) / (max_val - min_val) * 255
    return normalized.astype(np.uint8)


def apply_brightness_contrast(image: np.ndarray, brightness: int = 0, contrast: int = 0) -> np.ndarray:
    """Apply brightness and contrast adjustments to an image."""
    if image is None:
        return None
    if brightness != 0:
        if brightness > 0:
            shadow = brightness
            highlight = 255
        else:
            shadow = 0
            highlight = 255 + brightness
        alpha_b = (highlight - shadow) / 255
        gamma_b = shadow
        image = cv2.addWeighted(image, alpha_b, image, 0, gamma_b)
    if contrast != 0:
        f = 131 * (contrast + 127) / (127 * (131 - contrast))
        alpha_c = f
        gamma_c = 127 * (1 - f)
        image = cv2.addWeighted(image, alpha_c, image, 0, gamma_c)
    return np.clip(image, 0, 255).astype(np.uint8)


__all__ = [
    "numpy_to_base64",
    "base64_to_numpy",
    "normalize_image",
    "apply_brightness_contrast",
]
