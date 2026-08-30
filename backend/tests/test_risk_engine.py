from app.models.schemas import RiskInput
from app.services.risk_engine import risk_level, score_risk


def test_critical_risk_score():
    score = score_risk(RiskInput(1.0, 0.8, 0.9, 31, 0.1, 0.6))
    assert score >= 75
    assert risk_level(score) == "Critical"


def test_low_risk_score():
    score = score_risk(RiskInput(0.1, 0.1, 0.2, 18, 0.9, 0.1))
    assert score < 35
    assert risk_level(score) == "Low"

