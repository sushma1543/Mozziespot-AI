def explain_detection(days_persistent: int, ndwi: float, temperature: float, population_density: float, risk_level: str) -> list[str]:
    reasons = []
    if days_persistent >= 7:
        reasons.append(f"Water persisted for {days_persistent} days")
    if ndwi >= 0.35:
        reasons.append(f"NDWI confirms surface water signal ({ndwi:.2f})")
    if 24 <= temperature <= 34:
        reasons.append(f"Temperature is suitable for mosquito breeding ({temperature:.1f} C)")
    if population_density >= 0.65:
        reasons.append("Nearby population exposure is high")
    if risk_level in {"High", "Critical"}:
        reasons.append("Combined environmental indicators exceed intervention threshold")
    return reasons or ["Low combined evidence; continue monitoring"]


def recommendation_for(level: str) -> str:
    return {
        "Critical": "Inspect within 24 hours, drain stagnant water, apply larvicide if approved, and notify local health officers.",
        "High": "Schedule field inspection within 48 hours and prioritize sanitation crew assignment.",
        "Medium": "Monitor for persistence and inspect during routine sanitation rounds.",
        "Low": "No immediate intervention required; keep in weekly satellite watchlist.",
    }[level]

