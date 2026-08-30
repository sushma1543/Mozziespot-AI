import json
import math
import os

from flask import current_app

from app.models.schemas import Detection, RiskInput
from app.services.disease_engine import disease_suitability
from app.services.explainability import explain_detection, recommendation_for
from app.services.risk_engine import risk_level, score_risk


def _sample_path() -> str:
    return os.path.join(current_app.config["DATA_DIR"], "detections.geojson")


def load_raw_features() -> list[dict]:
    with open(_sample_path(), "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload["features"]


def build_detections() -> list[Detection]:
    detections = []
    for feature in load_raw_features():
        props = feature["properties"]
        lon, lat = feature["geometry"]["coordinates"]
        risk_input = RiskInput(
            water_persistence=props["water_persistence"],
            ndwi=props["ndwi"],
            population_density=props["population_density"],
            temperature=props["temperature"],
            building_distance=props["building_distance"],
            vegetation=props["vegetation"],
        )
        score = score_risk(risk_input)
        level = risk_level(score)
        breeding_likelihood = estimate_breeding_likelihood(score, props["days_persistent"], props["ndwi"])
        mosquito_activity_index = estimate_mosquito_activity(score, props["temperature"], props["population_density"])
        diseases = disease_suitability(score, props["temperature"], props["population_density"], 1 - props["building_distance"])
        reasons = explain_detection(props["days_persistent"], props["ndwi"], props["temperature"], props["population_density"], level)
        detections.append(
            Detection(
                id=props["id"],
                name=props["name"],
                latitude=lat,
                longitude=lon,
                confidence=props["confidence"],
                risk_score=score,
                risk_level=level,
                days_persistent=props["days_persistent"],
                ndwi=props["ndwi"],
                temperature=props["temperature"],
                population_density=props["population_density"],
                disease_index=diseases,
                breeding_likelihood=breeding_likelihood,
                mosquito_activity_index=mosquito_activity_index,
                habitat_type=classify_habitat(breeding_likelihood, mosquito_activity_index),
                reasons=reasons,
                recommendation=recommendation_for(level),
            )
        )
    return detections


def dashboard_summary() -> dict:
    detections = build_detections()
    high = [d for d in detections if d.risk_level in {"High", "Critical"}]
    avg_conf = round(sum(d.confidence for d in detections) / max(len(detections), 1), 2)
    disease_index = round(sum(max(d.disease_index.values()) for d in detections) / max(len(detections), 1), 1)
    return {
        "water_bodies": len(detections),
        "high_risk_zones": len(high),
        "alerts_sent": len(high),
        "ai_confidence": avg_conf,
        "disease_index": disease_index,
    }


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def estimate_breeding_likelihood(risk_score: float, days_persistent: int, ndwi: float) -> float:
    persistence_component = _clamp(days_persistent / 21) * 35
    water_component = _clamp(ndwi) * 25
    risk_component = _clamp(risk_score / 100) * 40
    return round(persistence_component + water_component + risk_component, 1)


def estimate_mosquito_activity(risk_score: float, temperature: float, population_density: float) -> float:
    temperature_score = 1.0 if 24 <= temperature <= 34 else 0.55
    exposure_score = _clamp(population_density)
    return round((0.55 * _clamp(risk_score / 100) + 0.25 * temperature_score + 0.20 * exposure_score) * 100, 1)


def classify_habitat(breeding_likelihood: float, mosquito_activity_index: float) -> str:
    if breeding_likelihood >= 75 and mosquito_activity_index >= 70:
        return "Probable breeding water body with high mosquito activity risk"
    if breeding_likelihood >= 55:
        return "Probable mosquito breeding water body"
    if mosquito_activity_index >= 55:
        return "Mosquito activity risk zone"
    return "Monitoring zone"


def _distance_meters(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    radius_m = 6371000
    phi_a = math.radians(lat_a)
    phi_b = math.radians(lat_b)
    delta_phi = math.radians(lat_b - lat_a)
    delta_lambda = math.radians(lon_b - lon_a)
    hav = math.sin(delta_phi / 2) ** 2 + math.cos(phi_a) * math.cos(phi_b) * math.sin(delta_lambda / 2) ** 2
    return 2 * radius_m * math.atan2(math.sqrt(hav), math.sqrt(1 - hav))


def _stable_noise(latitude: float, longitude: float) -> float:
    value = math.sin(latitude * 12.9898 + longitude * 78.233) * 43758.5453
    return value - math.floor(value)


def analyze_spot(latitude: float, longitude: float, name: str | None = None) -> Detection:
    features = load_raw_features()
    nearest = min(
        features,
        key=lambda feature: _distance_meters(
            latitude,
            longitude,
            feature["geometry"]["coordinates"][1],
            feature["geometry"]["coordinates"][0],
        ),
    )
    nearest_lon, nearest_lat = nearest["geometry"]["coordinates"]
    nearest_distance = _distance_meters(latitude, longitude, nearest_lat, nearest_lon)
    influence = _clamp(1 - nearest_distance / 2500)
    noise = _stable_noise(latitude, longitude)
    props = nearest["properties"]

    water_persistence = _clamp(0.18 + props["water_persistence"] * 0.72 * influence + noise * 0.10)
    ndwi = _clamp(0.16 + props["ndwi"] * 0.72 * influence + noise * 0.08)
    population_density = _clamp(0.25 + props["population_density"] * 0.70 * influence + noise * 0.10)
    temperature = round(27.2 + props["temperature"] * 0.08 + influence * 1.8 + noise * 1.4, 1)
    building_distance = _clamp(0.74 - (1 - props["building_distance"]) * 0.62 * influence + noise * 0.08)
    vegetation = _clamp(0.18 + props["vegetation"] * 0.55 * influence + (1 - influence) * 0.22)
    days_persistent = max(1, int(round(2 + water_persistence * 18)))

    risk_input = RiskInput(
        water_persistence=water_persistence,
        ndwi=ndwi,
        population_density=population_density,
        temperature=temperature,
        building_distance=building_distance,
        vegetation=vegetation,
    )
    score = score_risk(risk_input)
    level = risk_level(score)
    breeding_likelihood = estimate_breeding_likelihood(score, days_persistent, ndwi)
    mosquito_activity_index = estimate_mosquito_activity(score, temperature, population_density)
    diseases = disease_suitability(score, temperature, population_density, 1 - building_distance)
    reasons = explain_detection(days_persistent, ndwi, temperature, population_density, level)
    reasons.insert(0, "Analysis generated for user-selected coordinates")
    if nearest_distance <= 2500:
        reasons.append(f"Nearest known water evidence is {round(nearest_distance)} m away")
    else:
        reasons.append("No strong nearby sample water evidence; result is monitoring-grade")

    return Detection(
        id=f"SPOT-{abs(hash((round(latitude, 5), round(longitude, 5)))) % 100000}",
        name=name or f"Selected Spot {latitude:.4f}, {longitude:.4f}",
        latitude=latitude,
        longitude=longitude,
        confidence=round(0.62 + influence * 0.28, 2),
        risk_score=score,
        risk_level=level,
        days_persistent=days_persistent,
        ndwi=round(ndwi, 2),
        temperature=temperature,
        population_density=round(population_density, 2),
        disease_index=diseases,
        breeding_likelihood=breeding_likelihood,
        mosquito_activity_index=mosquito_activity_index,
        habitat_type=classify_habitat(breeding_likelihood, mosquito_activity_index),
        reasons=reasons,
        recommendation=recommendation_for(level),
    )


def search_mosquito_habitats(query: str = "", minimum: str = "Medium") -> list[dict]:
    order = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
    minimum_rank = order.get(minimum, 1)
    lowered = query.strip().lower()
    results = []
    for detection in build_detections():
        if order[detection.risk_level] < minimum_rank and detection.breeding_likelihood < 45:
            continue
        if lowered and lowered not in detection.name.lower() and lowered not in detection.risk_level.lower() and lowered not in detection.habitat_type.lower():
            continue
        results.append(detection.to_dict())
    return sorted(
        results,
        key=lambda item: (item["breeding_likelihood"], item["mosquito_activity_index"], item["risk_score"]),
        reverse=True,
    )
