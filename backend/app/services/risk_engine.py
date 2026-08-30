from app.models.schemas import RiskInput


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def normalize_temperature(celsius: float) -> float:
    if celsius <= 18:
        return 0.1
    if celsius >= 34:
        return 0.95
    return clamp((celsius - 18) / 16)


def score_risk(values: RiskInput) -> float:
    temp_score = normalize_temperature(values.temperature)
    building_score = 1 - clamp(values.building_distance)
    score = (
        0.30 * clamp(values.water_persistence)
        + 0.20 * clamp(values.ndwi)
        + 0.20 * clamp(values.population_density)
        + 0.15 * temp_score
        + 0.10 * building_score
        + 0.05 * clamp(values.vegetation)
    )
    return round(score * 100, 2)


def risk_level(score: float) -> str:
    if score >= 75:
        return "Critical"
    if score >= 55:
        return "High"
    if score >= 35:
        return "Medium"
    return "Low"

