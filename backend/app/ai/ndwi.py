import numpy as np


def compute_ndwi(green_band: np.ndarray, nir_band: np.ndarray) -> np.ndarray:
    green = green_band.astype("float32")
    nir = nir_band.astype("float32")
    return (green - nir) / (green + nir + 1e-6)


def water_mask_from_ndwi(ndwi: np.ndarray, threshold: float = 0.30) -> np.ndarray:
    return (ndwi >= threshold).astype("uint8")

