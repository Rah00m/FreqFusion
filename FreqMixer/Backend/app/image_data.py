"""
ImageData dataclass module.

Defines the immutable structure for storing per-image metadata and Fourier Transform components.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np

try:
    from .ft_transformer import FTComponents
except ImportError:
    from ft_transformer import FTComponents


@dataclass
class ImageData:
    """Data container for an individual image and its FT components."""
    id: int
    path: str = ""
    original: Optional[np.ndarray] = None
    current: Optional[np.ndarray] = None
    loaded: bool = False
    size: Tuple[int, int] = (0, 0)  # (width, height)

    # Full FT components object
    ft_components: Optional[FTComponents] = None

    def has_ft_components(self) -> bool:
        return self.ft_components is not None

    def get_ft_display(self, component_name: str) -> Optional[np.ndarray]:
        if not self.has_ft_components():
            return None
        return self.ft_components.get_display_component(component_name)

    def get_ft_raw(self, component_name: str) -> Optional[np.ndarray]:
        if not self.has_ft_components():
            return None
        return self.ft_components.get_raw_component(component_name)