"""
Spectral index calculations for Sentinel-2 bands.
"""

from __future__ import annotations

import numpy as np


EPSILON = 1e-6


def normalized_difference(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (a.astype("float32") - b.astype("float32")) / (a.astype("float32") + b.astype("float32") + EPSILON)


def ndwi(green_b03: np.ndarray, nir_b08: np.ndarray) -> np.ndarray:
    return normalized_difference(green_b03, nir_b08)


def mndwi(green_b03: np.ndarray, swir_b11: np.ndarray) -> np.ndarray:
    return normalized_difference(green_b03, swir_b11)


def ndvi(nir_b08: np.ndarray, red_b04: np.ndarray) -> np.ndarray:
    return normalized_difference(nir_b08, red_b04)


def water_mask(ndwi_image: np.ndarray, threshold: float = 0.30) -> np.ndarray:
    return (ndwi_image >= threshold).astype("uint8")
