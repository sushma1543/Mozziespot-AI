"""
Segmentation ensemble helper.

The production app can combine U-Net, DeepLabV3+, and SegFormer masks by
weighted averaging, then threshold the final probability map.
"""

from __future__ import annotations

from typing import Iterable

import numpy as np


def ensemble_probability(masks: Iterable[np.ndarray], weights: Iterable[float] | None = None) -> np.ndarray:
    masks = [mask.astype("float32") for mask in masks]
    if not masks:
        raise ValueError("at least one mask is required")
    if weights is None:
        weights = [1.0 / len(masks)] * len(masks)
    weights = list(weights)
    total = max(sum(weights), 1e-6)
    normalized = [weight / total for weight in weights]
    output = np.zeros_like(masks[0], dtype="float32")
    for mask, weight in zip(masks, normalized):
        output += mask * weight
    return np.clip(output, 0, 1)


def ensemble_mask(masks: Iterable[np.ndarray], threshold: float = 0.5, weights: Iterable[float] | None = None) -> np.ndarray:
    return (ensemble_probability(masks, weights) >= threshold).astype("uint8")
