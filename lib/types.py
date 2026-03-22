'''Type aliases for array types used throughout the QFab pipeline.'''
import numpy as np
from numpy.typing import NDArray


__all__ = 'Field Hologram Shape Position Displacement'.split()


# 2D complex array produced by the CGH pipeline.
# dtype is np.complex64 by default; subclasses may use np.complex128.
Field = np.ndarray

# Quantized phase hologram (uint8) ready for display on the SLM.
Hologram = NDArray[np.uint8]

# Hologram and SLM dimensions: (height, width) in pixels.
Shape = tuple[int, int]

# Three-dimensional trap position [pixels]: (x, y, z).
Position = NDArray[np.float64]

# Three-dimensional displacement vector [pixels]: (dx, dy, dz).
Displacement = NDArray[np.float64]
