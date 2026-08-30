from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class RiskInput:
    water_persistence: float
    ndwi: float
    population_density: float
    temperature: float
    building_distance: float
    vegetation: float


@dataclass
class Detection:
    id: str
    name: str
    latitude: float
    longitude: float
    confidence: float
    risk_score: float
    risk_level: str
    days_persistent: int
    ndwi: float
    temperature: float
    population_density: float
    disease_index: dict[str, float]
    breeding_likelihood: float
    mosquito_activity_index: float
    habitat_type: str
    reasons: list[str]
    recommendation: str
    state: str = "Telangana"
    district: str = "Hyderabad"
    village: str = "Demo Ward"
    authority_type: str = "Municipality"
    authority_name: str = "GHMC"
    last_updated: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
