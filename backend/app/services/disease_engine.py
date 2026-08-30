def disease_suitability(risk_score: float, temperature: float, population_density: float, urban_factor: float) -> dict[str, float]:
    base = risk_score / 100
    warm = 1.0 if 24 <= temperature <= 34 else 0.55
    urban = max(0.0, min(1.0, urban_factor))
    population = max(0.0, min(1.0, population_density))
    return {
        "malaria": round(100 * base * warm, 1),
        "dengue": round(100 * base * max(urban, population), 1),
        "chikungunya": round(100 * base * (0.55 + 0.45 * urban), 1),
        "diarrhea": round(100 * base * 0.72, 1),
        "cholera": round(100 * base * 0.58, 1),
        "typhoid": round(100 * base * 0.50, 1),
    }

