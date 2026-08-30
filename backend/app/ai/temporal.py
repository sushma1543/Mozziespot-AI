import numpy as np


def persistence_score(masks: list[np.ndarray]) -> float:
    if not masks:
        return 0.0
    stacked = np.stack(masks, axis=0)
    persistent = stacked.mean(axis=0)
    return float(persistent.mean())


def persistent_water_mask(masks: list[np.ndarray], minimum_presence: float = 0.50) -> np.ndarray:
    if not masks:
        raise ValueError("At least one mask is required")
    return (np.stack(masks, axis=0).mean(axis=0) >= minimum_presence).astype("uint8")

