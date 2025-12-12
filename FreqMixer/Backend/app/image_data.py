"""
ImageData dataclass module.

Defines the immutable structure for storing per-image metadata and transform components.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np


@dataclass
class ImageData:
    """Data container for an individual image and its metadata."""
    id: int
    path: str = ""
    original: Optional[np.ndarray] = None
    current: Optional[np.ndarray] = None
    loaded: bool = False
    size: Tuple[int, int] = (0, 0)  # (width, height)
    ft_magnitude: Optional[np.ndarray] = None
    ft_phase: Optional[np.ndarray] = None
    ft_real: Optional[np.ndarray] = None
    ft_imaginary: Optional[np.ndarray] = None
