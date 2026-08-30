"""Research-validation utilities for segmentation experiments.

These functions never manufacture model scores. Metrics are returned only when
ground-truth labels and predictions are supplied by an experiment.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
import json
import math

import numpy as np


MODEL_NAMES = ("U-Net", "DeepLabV3+", "SegFormer", "Ensemble")
WEIGHT_FILES = {
    "U-Net": "unet.pt",
    "DeepLabV3+": "deeplabv3plus.pt",
    "SegFormer": "segformer.pt",
}


def _json_safe(value):
    """Replace NaN/Infinity from experiment artifacts with valid JSON nulls."""
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def confusion_counts(actual: Iterable[int], predicted: Iterable[int]) -> dict[str, int]:
    truth = np.asarray(actual, dtype=np.uint8).reshape(-1)
    guess = np.asarray(predicted, dtype=np.uint8).reshape(-1)
    if truth.shape != guess.shape or truth.size == 0:
        raise ValueError("actual and predicted masks must be non-empty and have equal shape")
    if not np.isin(truth, [0, 1]).all() or not np.isin(guess, [0, 1]).all():
        raise ValueError("masks must contain only binary values 0 and 1")
    return {
        "tp": int(np.sum((truth == 1) & (guess == 1))),
        "fp": int(np.sum((truth == 0) & (guess == 1))),
        "fn": int(np.sum((truth == 1) & (guess == 0))),
        "tn": int(np.sum((truth == 0) & (guess == 0))),
    }


def _ratio(numerator: float, denominator: float) -> float | None:
    return round(float(numerator / denominator), 6) if denominator else None


def segmentation_metrics(actual: Iterable[int], predicted: Iterable[int]) -> dict:
    counts = confusion_counts(actual, predicted)
    tp, fp, fn, tn = (counts[key] for key in ("tp", "fp", "fn", "tn"))
    precision = _ratio(tp, tp + fp)
    recall = _ratio(tp, tp + fn)
    return {
        "confusion_matrix": counts,
        "precision": precision,
        "recall": recall,
        "sensitivity": recall,
        "specificity": _ratio(tn, tn + fp),
        "accuracy": _ratio(tp + tn, tp + tn + fp + fn),
        "f1": _ratio(2 * tp, 2 * tp + fp + fn),
        "iou": _ratio(tp, tp + fp + fn),
        "dice": _ratio(2 * tp, 2 * tp + fp + fn),
    }


def threshold_curves(actual: Iterable[int], probabilities: Iterable[float], steps: int = 21) -> dict:
    truth = np.asarray(actual, dtype=np.uint8).reshape(-1)
    scores = np.asarray(probabilities, dtype=float).reshape(-1)
    if truth.shape != scores.shape or truth.size == 0:
        raise ValueError("actual labels and probabilities must be non-empty and have equal shape")
    if not np.isin(truth, [0, 1]).all() or np.any((scores < 0) | (scores > 1)):
        raise ValueError("labels must be binary and probabilities must be between 0 and 1")
    roc, precision_recall = [], []
    for threshold in np.linspace(0, 1, steps):
        metrics = segmentation_metrics(truth, (scores >= threshold).astype(np.uint8))
        cm = metrics["confusion_matrix"]
        fpr = _ratio(cm["fp"], cm["fp"] + cm["tn"])
        roc.append({"threshold": round(float(threshold), 3), "tpr": metrics["recall"], "fpr": fpr})
        precision_recall.append(
            {"threshold": round(float(threshold), 3), "precision": metrics["precision"], "recall": metrics["recall"]}
        )
    return {"roc": roc, "precision_recall": precision_recall}


def calibration_bins(actual: Iterable[int], probabilities: Iterable[float], bins: int = 10) -> dict:
    truth = np.asarray(actual, dtype=np.uint8).reshape(-1)
    scores = np.asarray(probabilities, dtype=float).reshape(-1)
    if truth.shape != scores.shape or truth.size == 0:
        raise ValueError("actual labels and probabilities must be non-empty and have equal shape")
    rows, ece = [], 0.0
    for index in range(bins):
        low, high = index / bins, (index + 1) / bins
        selected = (scores >= low) & (scores <= high if index == bins - 1 else scores < high)
        if not selected.any():
            continue
        confidence = float(scores[selected].mean())
        observed = float(truth[selected].mean())
        count = int(selected.sum())
        ece += count / truth.size * abs(confidence - observed)
        rows.append({"from": low, "to": high, "count": count, "confidence": round(confidence, 6), "observed": round(observed, 6)})
    return {
        "bins": rows,
        "expected_calibration_error": round(ece, 6),
        "brier_score": round(float(np.mean((scores - truth) ** 2)), 6),
    }


def deterministic_split(ids: Iterable[str], train: float = 0.7, validation: float = 0.15) -> dict[str, list[str]]:
    """Stable split by sample id; callers should group by geography before use."""
    result = {"training": [], "validation": [], "test": []}
    for sample_id in sorted(set(ids)):
        bucket = int.from_bytes(sample_id.encode("utf-8"), "little") % 10_000 / 10_000
        key = "training" if bucket < train else "validation" if bucket < train + validation else "test"
        result[key].append(sample_id)
    return result


def validation_status(backend_root: Path) -> dict:
    weights_dir = backend_root / "model_weights"
    dataset_dir = backend_root.parent / "datasets" / "sen1floods11"
    model_status = []
    for name in MODEL_NAMES:
        required = [] if name == "Ensemble" else [str(weights_dir / WEIGHT_FILES[name])]
        ready = name == "Ensemble" and all((weights_dir / filename).is_file() for filename in WEIGHT_FILES.values())
        if name != "Ensemble":
            ready = Path(required[0]).is_file()
        model_status.append({"name": name, "trained_weights": ready, "required_files": required})
    labels_ready = dataset_dir.is_dir() and any(dataset_dir.rglob("*_LabelHand.tif")) and any(dataset_dir.rglob("*_S2Hand.tif"))
    report_path = backend_root / "experiments" / "latest.json"
    experiment = None
    if report_path.is_file():
        try:
            experiment = _json_safe(json.loads(report_path.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError):
            experiment = None
    return {
        "mode": "experimental_validation",
        "operational_map_source": "Sentinel spectral indices plus deterministic environmental risk rules",
        "validated_model_inference": any(item["trained_weights"] for item in model_status),
        "ground_truth_ready": labels_ready,
        "dataset_path": str(dataset_dir),
        "models": model_status,
        "experiment": experiment,
        "experiment_report": str(report_path),
        "available_when_data_supplied": [
            "train/validation/test split",
            "confusion matrix",
            "precision, recall, F1, accuracy, specificity, IoU and Dice",
            "ROC and precision-recall curves",
            "calibration bins, ECE and Brier score",
            "cross-validation, hyperparameter and ablation experiment recording",
            "field and epidemiological validation manifests",
        ],
        "not_claimed": [
            "clinical disease probability",
            "field-validated mosquito detection accuracy",
            "trained DeepLabV3+, SegFormer or ensemble output without weight files",
            "production PostGIS, RBAC, scheduler or WhatsApp Business delivery",
        ],
    }
