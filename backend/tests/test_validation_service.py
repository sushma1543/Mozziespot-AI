from app.services.validation_service import _json_safe, calibration_bins, deterministic_split, segmentation_metrics, threshold_curves


def test_segmentation_metrics():
    metrics = segmentation_metrics([1, 1, 0, 0], [1, 0, 1, 0])
    assert metrics["confusion_matrix"] == {"tp": 1, "fp": 1, "fn": 1, "tn": 1}
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5
    assert metrics["iou"] == 0.333333
    assert metrics["dice"] == 0.5


def test_curves_and_calibration_are_computed_from_supplied_labels():
    curves = threshold_curves([0, 0, 1, 1], [0.1, 0.4, 0.7, 0.9], steps=3)
    calibration = calibration_bins([0, 0, 1, 1], [0.1, 0.4, 0.7, 0.9], bins=2)
    assert len(curves["roc"]) == 3
    assert calibration["brier_score"] == 0.0675


def test_split_is_stable_and_complete():
    ids = [f"scene-{index}" for index in range(40)]
    first = deterministic_split(ids)
    second = deterministic_split(reversed(ids))
    assert first == second
    assert sorted(first["training"] + first["validation"] + first["test"]) == sorted(ids)


def test_non_finite_experiment_values_are_valid_json_nulls():
    assert _json_safe({"loss": float("nan"), "curve": [0.5, float("inf")]}) == {
        "loss": None,
        "curve": [0.5, None],
    }
