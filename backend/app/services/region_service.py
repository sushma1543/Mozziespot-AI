import datetime as dt
import math
import os
from functools import lru_cache

import requests

from app.models.schemas import Detection, RiskInput
from app.services.disease_engine import disease_suitability
from app.services.explainability import explain_detection, recommendation_for
from app.services.risk_engine import risk_level, score_risk


STATE_CENTERS = {
    "Telangana": (17.8496, 79.1152),
    "Andhra Pradesh": (15.9129, 79.7400),
}


DISTRICTS = {
    "Telangana": [
        ("Adilabad", 19.6667, 78.5333), ("Bhadradri Kothagudem", 17.5544, 80.6197),
        ("Hanumakonda", 18.0072, 79.5584), ("Hyderabad", 17.3850, 78.4867),
        ("Jagtial", 18.7909, 78.9138), ("Jangaon", 17.7260, 79.1520),
        ("Jayashankar Bhupalpally", 18.4290, 79.8670), ("Jogulamba Gadwal", 16.2350, 77.8050),
        ("Kamareddy", 18.3205, 78.3370), ("Karimnagar", 18.4386, 79.1288),
        ("Khammam", 17.2473, 80.1514), ("Kumuram Bheem Asifabad", 19.3650, 79.2740),
        ("Mahabubabad", 17.5988, 80.0020), ("Mahabubnagar", 16.7488, 78.0035),
        ("Mancherial", 18.8756, 79.4591), ("Medak", 18.0458, 78.2608),
        ("Medchal-Malkajgiri", 17.6310, 78.4810), ("Mulugu", 18.1910, 79.9430),
        ("Nagarkurnool", 16.4827, 78.3247), ("Nalgonda", 17.0575, 79.2684),
        ("Narayanpet", 16.7480, 77.4950), ("Nirmal", 19.0964, 78.3441),
        ("Nizamabad", 18.6725, 78.0941), ("Peddapalli", 18.6151, 79.3832),
        ("Rajanna Sircilla", 18.3864, 78.8022), ("Rangareddy", 17.2403, 78.4294),
        ("Sangareddy", 17.6194, 78.0823), ("Siddipet", 18.1018, 78.8520),
        ("Suryapet", 17.1405, 79.6205), ("Vikarabad", 17.3381, 77.9044),
        ("Wanaparthy", 16.3623, 78.0622), ("Warangal", 17.9689, 79.5941),
        ("Yadadri Bhuvanagiri", 17.5150, 78.8856),
    ],
    "Andhra Pradesh": [
        ("Alluri Sitharama Raju", 17.8600, 82.3500), ("Anakapalli", 17.6913, 83.0039),
        ("Ananthapuramu", 14.6819, 77.6006), ("Annamayya", 14.2500, 78.7500),
        ("Bapatla", 15.9042, 80.4674), ("Chittoor", 13.2172, 79.1003),
        ("Dr B R Ambedkar Konaseema", 16.5600, 82.0500), ("East Godavari", 17.0005, 81.8040),
        ("Eluru", 16.7107, 81.0952), ("Guntur", 16.3067, 80.4365),
        ("Kakinada", 16.9891, 82.2475), ("Krishna", 16.6100, 80.7214),
        ("Kurnool", 15.8281, 78.0373), ("Nandyal", 15.4777, 78.4836),
        ("NTR", 16.5062, 80.6480), ("Palnadu", 16.2350, 79.7400),
        ("Parvathipuram Manyam", 18.7830, 83.4250), ("Prakasam", 15.5057, 80.0499),
        ("Sri Potti Sriramulu Nellore", 14.4426, 79.9865), ("Sri Sathya Sai", 14.1667, 77.8117),
        ("Srikakulam", 18.2969, 83.8968), ("Tirupati", 13.6288, 79.4192),
        ("Visakhapatnam", 17.6868, 83.2185), ("Vizianagaram", 18.1067, 83.3956),
        ("West Godavari", 16.5449, 81.5212), ("YSR", 14.4673, 78.8242),
    ],
}


PLACE_GAZETTEER = [
    {"name": "VIT-AP University", "state": "Andhra Pradesh", "district": "Guntur", "village": "Mandadam", "lat": 16.4961, "lon": 80.5007, "aliases": ["vitap", "vit ap", "vit-ap", "mandadam vitap", "vit university amaravati"]},
    {"name": "Mandadam", "state": "Andhra Pradesh", "district": "Guntur", "village": "Mandadam", "lat": 16.5067, "lon": 80.5079, "aliases": ["mandadam", "mandadam village"]},
    {"name": "Amaravati", "state": "Andhra Pradesh", "district": "Guntur", "village": "Amaravati", "lat": 16.5131, "lon": 80.5165, "aliases": ["amaravathi", "amaravati capital"]},
    {"name": "Tullur", "state": "Andhra Pradesh", "district": "Guntur", "village": "Tullur", "lat": 16.5246, "lon": 80.4547, "aliases": ["thullur", "tulluru"]},
    {"name": "Mangalagiri", "state": "Andhra Pradesh", "district": "Guntur", "village": "Mangalagiri", "lat": 16.4309, "lon": 80.5686, "aliases": ["mangalagiri town"]},
    {"name": "Guntur", "state": "Andhra Pradesh", "district": "Guntur", "village": "Guntur Urban", "lat": 16.3067, "lon": 80.4365, "aliases": ["guntur city"]},
    {"name": "Vijayawada", "state": "Andhra Pradesh", "district": "NTR", "village": "Vijayawada Urban", "lat": 16.5062, "lon": 80.6480, "aliases": ["bezawada", "vijayawada city"]},
    {"name": "Tenali", "state": "Andhra Pradesh", "district": "Guntur", "village": "Tenali", "lat": 16.2395, "lon": 80.6493, "aliases": ["tenali town"]},
    {"name": "Visakhapatnam", "state": "Andhra Pradesh", "district": "Visakhapatnam", "village": "Vizag Urban", "lat": 17.6868, "lon": 83.2185, "aliases": ["vizag", "visakhapatnam city"]},
    {"name": "Tirupati", "state": "Andhra Pradesh", "district": "Tirupati", "village": "Tirupati Urban", "lat": 13.6288, "lon": 79.4192, "aliases": ["tirupathi"]},
    {"name": "Kakinada", "state": "Andhra Pradesh", "district": "Kakinada", "village": "Kakinada Urban", "lat": 16.9891, "lon": 82.2475, "aliases": ["kakinada city"]},
    {"name": "Rajamahendravaram", "state": "Andhra Pradesh", "district": "East Godavari", "village": "Rajamahendravaram", "lat": 17.0005, "lon": 81.8040, "aliases": ["rajahmundry", "rajamahendravaram"]},
    {"name": "Nellore", "state": "Andhra Pradesh", "district": "Sri Potti Sriramulu Nellore", "village": "Nellore Urban", "lat": 14.4426, "lon": 79.9865, "aliases": ["nellore city"]},
    {"name": "Kurnool", "state": "Andhra Pradesh", "district": "Kurnool", "village": "Kurnool Urban", "lat": 15.8281, "lon": 78.0373, "aliases": ["kurnool city"]},
    {"name": "Anantapur", "state": "Andhra Pradesh", "district": "Ananthapuramu", "village": "Anantapur Urban", "lat": 14.6819, "lon": 77.6006, "aliases": ["ananthapur", "ananthapuramu"]},
    {"name": "Hyderabad", "state": "Telangana", "district": "Hyderabad", "village": "Hyderabad Urban", "lat": 17.3850, "lon": 78.4867, "aliases": ["hyderabad city", "ghmc"]},
    {"name": "Secunderabad", "state": "Telangana", "district": "Hyderabad", "village": "Secunderabad", "lat": 17.4399, "lon": 78.4983, "aliases": ["secunderabad city"]},
    {"name": "Kukatpally", "state": "Telangana", "district": "Medchal-Malkajgiri", "village": "Kukatpally", "lat": 17.4948, "lon": 78.3996, "aliases": ["kphb", "kukatpally housing board"]},
    {"name": "Gachibowli", "state": "Telangana", "district": "Rangareddy", "village": "Gachibowli", "lat": 17.4401, "lon": 78.3489, "aliases": ["financial district", "hitech city near"]},
    {"name": "Uppal", "state": "Telangana", "district": "Medchal-Malkajgiri", "village": "Uppal", "lat": 17.4058, "lon": 78.5591, "aliases": ["uppal kalan"]},
    {"name": "Warangal", "state": "Telangana", "district": "Warangal", "village": "Warangal Urban", "lat": 17.9689, "lon": 79.5941, "aliases": ["warangal city"]},
    {"name": "Karimnagar", "state": "Telangana", "district": "Karimnagar", "village": "Karimnagar Urban", "lat": 18.4386, "lon": 79.1288, "aliases": ["karimnagar city"]},
    {"name": "Khammam", "state": "Telangana", "district": "Khammam", "village": "Khammam Urban", "lat": 17.2473, "lon": 80.1514, "aliases": ["khammam city"]},
    {"name": "Nizamabad", "state": "Telangana", "district": "Nizamabad", "village": "Nizamabad Urban", "lat": 18.6725, "lon": 78.0941, "aliases": ["nizamabad city"]},
    {"name": "Nalgonda", "state": "Telangana", "district": "Nalgonda", "village": "Nalgonda Urban", "lat": 17.0575, "lon": 79.2684, "aliases": ["nalgonda city"]}
]


PLACE_GAZETTEER.extend([
    {"name": "Penamaluru", "state": "Andhra Pradesh", "district": "Krishna", "village": "Penamaluru", "lat": 16.4639, "lon": 80.7177, "aliases": ["penamaluru mandal"]},
    {"name": "Poranki", "state": "Andhra Pradesh", "district": "Krishna", "village": "Poranki", "lat": 16.4738, "lon": 80.7115, "aliases": ["poranki vijayawada"]},
    {"name": "Ibrahimpatnam", "state": "Andhra Pradesh", "district": "NTR", "village": "Ibrahimpatnam", "lat": 16.5884, "lon": 80.5222, "aliases": ["ibrahimpatnam ap"]},
    {"name": "Kondapalli", "state": "Andhra Pradesh", "district": "NTR", "village": "Kondapalli", "lat": 16.6199, "lon": 80.5428, "aliases": ["kondapalli fort"]},
    {"name": "Namburu", "state": "Andhra Pradesh", "district": "Guntur", "village": "Namburu", "lat": 16.3546, "lon": 80.5281, "aliases": ["nambur"]},
    {"name": "Pedakakani", "state": "Andhra Pradesh", "district": "Guntur", "village": "Pedakakani", "lat": 16.3465, "lon": 80.4894, "aliases": ["pedakakani village"]},
    {"name": "Duggirala", "state": "Andhra Pradesh", "district": "Guntur", "village": "Duggirala", "lat": 16.3271, "lon": 80.6257, "aliases": ["duggirala mandal"]},
    {"name": "Undavalli", "state": "Andhra Pradesh", "district": "Guntur", "village": "Undavalli", "lat": 16.4964, "lon": 80.5800, "aliases": ["undavalli caves"]},
    {"name": "Kaza", "state": "Andhra Pradesh", "district": "Guntur", "village": "Kaza", "lat": 16.4198, "lon": 80.5351, "aliases": ["kaza village"]},
    {"name": "Tadepalli", "state": "Andhra Pradesh", "district": "Guntur", "village": "Tadepalli", "lat": 16.4835, "lon": 80.6005, "aliases": ["tadepalli guntur"]},
    {"name": "Gannavaram", "state": "Andhra Pradesh", "district": "Krishna", "village": "Gannavaram", "lat": 16.5409, "lon": 80.8025, "aliases": ["gannavaram airport"]},
    {"name": "Gudivada", "state": "Andhra Pradesh", "district": "Krishna", "village": "Gudivada", "lat": 16.4350, "lon": 80.9950, "aliases": ["gudivada town"]},
    {"name": "Machilipatnam", "state": "Andhra Pradesh", "district": "Krishna", "village": "Machilipatnam", "lat": 16.1875, "lon": 81.1389, "aliases": ["masulipatnam", "machilipatnam town"]},
    {"name": "Bhimavaram", "state": "Andhra Pradesh", "district": "West Godavari", "village": "Bhimavaram", "lat": 16.5449, "lon": 81.5212, "aliases": ["bhimavaram town"]},
    {"name": "Eluru", "state": "Andhra Pradesh", "district": "Eluru", "village": "Eluru Urban", "lat": 16.7107, "lon": 81.0952, "aliases": ["eluru city"]},
    {"name": "Ongole", "state": "Andhra Pradesh", "district": "Prakasam", "village": "Ongole Urban", "lat": 15.5057, "lon": 80.0499, "aliases": ["ongole city"]},
    {"name": "Kadapa", "state": "Andhra Pradesh", "district": "YSR", "village": "Kadapa Urban", "lat": 14.4673, "lon": 78.8242, "aliases": ["cuddapah", "kadapa city"]},
    {"name": "Madhapur", "state": "Telangana", "district": "Rangareddy", "village": "Madhapur", "lat": 17.4483, "lon": 78.3915, "aliases": ["hitech city", "hitex"]},
    {"name": "Miyapur", "state": "Telangana", "district": "Medchal-Malkajgiri", "village": "Miyapur", "lat": 17.4965, "lon": 78.3618, "aliases": ["miyapur hyderabad"]},
    {"name": "Bachupally", "state": "Telangana", "district": "Medchal-Malkajgiri", "village": "Bachupally", "lat": 17.5449, "lon": 78.3468, "aliases": ["bachupally hyderabad"]},
    {"name": "Kondapur", "state": "Telangana", "district": "Rangareddy", "village": "Kondapur", "lat": 17.4698, "lon": 78.3578, "aliases": ["kondapur hyderabad"]},
    {"name": "Dilsukhnagar", "state": "Telangana", "district": "Hyderabad", "village": "Dilsukhnagar", "lat": 17.3687, "lon": 78.5247, "aliases": ["dilsukhnagar hyderabad"]},
    {"name": "LB Nagar", "state": "Telangana", "district": "Rangareddy", "village": "LB Nagar", "lat": 17.3457, "lon": 78.5522, "aliases": ["l b nagar", "lbnagar"]},
    {"name": "Kompally", "state": "Telangana", "district": "Medchal-Malkajgiri", "village": "Kompally", "lat": 17.5417, "lon": 78.4810, "aliases": ["kompally hyderabad"]},
    {"name": "Shamshabad", "state": "Telangana", "district": "Rangareddy", "village": "Shamshabad", "lat": 17.2512, "lon": 78.4377, "aliases": ["rajiv gandhi airport"]}
])


ZONE_TEMPLATES = [
    ("Urban Drain / Ward", 0.012, 0.016, 0.82, 0.72, 0.88, 0.18, 0.28),
    ("Village Tank / Cheruvu", -0.018, 0.009, 0.76, 0.68, 0.54, 0.44, 0.62),
    ("Canal / Low-Lying Field", 0.020, -0.021, 0.62, 0.52, 0.43, 0.58, 0.78),
]



PLACE_GAZETTEER.extend([
    {"name": "Velagapudi", "state": "Andhra Pradesh", "district": "Guntur", "village": "Velagapudi", "lat": 16.5227, "lon": 80.5155, "aliases": ["velagapudi secretariat", "ap secretariat", "andhra pradesh secretariat"]},
    {"name": "Ainavolu", "state": "Andhra Pradesh", "district": "Guntur", "village": "Ainavolu", "lat": 16.4808, "lon": 80.4868, "aliases": ["ainavolu village", "inavolu"]},
    {"name": "Nelapadu", "state": "Andhra Pradesh", "district": "Guntur", "village": "Nelapadu", "lat": 16.5083, "lon": 80.4666, "aliases": ["nelapadu village"]},
    {"name": "Rayapudi", "state": "Andhra Pradesh", "district": "Guntur", "village": "Rayapudi", "lat": 16.5482, "lon": 80.4914, "aliases": ["rayapudi village"]},
    {"name": "Lingayapalem", "state": "Andhra Pradesh", "district": "Guntur", "village": "Lingayapalem", "lat": 16.5346, "lon": 80.4649, "aliases": ["lingayapalem village"]},
    {"name": "Uddandarayunipalem", "state": "Andhra Pradesh", "district": "Guntur", "village": "Uddandarayunipalem", "lat": 16.5711, "lon": 80.4507, "aliases": ["uddandarayuni palem", "uddandarayunipalem village"]},
    {"name": "Krishnayapalem", "state": "Andhra Pradesh", "district": "Guntur", "village": "Krishnayapalem", "lat": 16.5036, "lon": 80.5690, "aliases": ["krishna y palem", "krishnaya palem"]},
    {"name": "Venkatapalem", "state": "Andhra Pradesh", "district": "Guntur", "village": "Venkatapalem", "lat": 16.5264, "lon": 80.5497, "aliases": ["venkata palem", "venkatapalem village"]},
    {"name": "Kuragallu", "state": "Andhra Pradesh", "district": "Guntur", "village": "Kuragallu", "lat": 16.4855, "lon": 80.5303, "aliases": ["kuragallu village"]},
    {"name": "Neerukonda", "state": "Andhra Pradesh", "district": "Guntur", "village": "Neerukonda", "lat": 16.4462, "lon": 80.5455, "aliases": ["nirukonda", "neerukonda village"]},
    {"name": "Bethapudi", "state": "Andhra Pradesh", "district": "Guntur", "village": "Bethapudi", "lat": 16.4623, "lon": 80.5205, "aliases": ["bethapudi village"]},
    {"name": "Abbarajupalem", "state": "Andhra Pradesh", "district": "Guntur", "village": "Abbarajupalem", "lat": 16.5447, "lon": 80.4388, "aliases": ["abbara ju palem", "abbarajupalem village"]},
    {"name": "Malkapuram", "state": "Andhra Pradesh", "district": "Guntur", "village": "Malkapuram", "lat": 16.5639, "lon": 80.4724, "aliases": ["malkapuram amaravati"]},
    {"name": "Dondapadu", "state": "Andhra Pradesh", "district": "Guntur", "village": "Dondapadu", "lat": 16.4960, "lon": 80.4321, "aliases": ["dondapadu village"]},
    {"name": "Pitchukalapalem", "state": "Andhra Pradesh", "district": "Guntur", "village": "Pitchukalapalem", "lat": 16.5201, "lon": 80.4279, "aliases": ["pitchukala palem"]},
    {"name": "Sakhamuru", "state": "Andhra Pradesh", "district": "Guntur", "village": "Sakhamuru", "lat": 16.4760, "lon": 80.4847, "aliases": ["sakhamuru village"]}
])


def _normalize_text(value: str) -> str:
    cleaned = []
    for char in value.lower():
        cleaned.append(char if char.isalnum() else " ")
    return " ".join("".join(cleaned).split())


def _query_matches(query: str, blob: str) -> bool:
    normalized_query = _normalize_text(query)
    if not normalized_query:
        return True
    normalized_blob = _normalize_text(blob)
    tokens = normalized_query.split()
    return all(token in normalized_blob for token in tokens)


def _place_matches(place: dict, query: str) -> bool:
    blob = " ".join([place["name"], place["state"], place["district"], place["village"], *place.get("aliases", [])])
    return _query_matches(query, blob)


def _geocode_candidate_score(candidate: dict, query: str, state: str = "", district: str = "") -> int:
    display = _normalize_text(candidate.get("display_name", ""))
    name = _normalize_text(candidate.get("name", ""))
    query_text = _normalize_text(query)
    tokens = query_text.split()
    score = 0
    if query_text and name == query_text:
        score += 80
    if tokens and all(token in display for token in tokens):
        score += 45
    if query_text and query_text in display:
        score += 25
    if state and state != "All" and _normalize_text(state) in display:
        score += 15
    if district and district != "All" and _normalize_text(district) in display:
        score += 15
    if "andhra pradesh" in display or "telangana" in display:
        score += 20
    address = candidate.get("address", {})
    if address.get("village") or address.get("town") or address.get("city") or address.get("suburb"):
        score += 8
    return score


def _requested_place_name(query: str) -> str:
    return _normalize_text(query.split(",", 1)[0])


def _nominatim_exact_match(candidate: dict, query: str) -> bool:
    requested = _requested_place_name(query)
    if not requested:
        return False
    address = candidate.get("address", {})
    names = [
        candidate.get("name"),
        address.get("village"),
        address.get("town"),
        address.get("city"),
        address.get("municipality"),
        address.get("suburb"),
        address.get("hamlet"),
    ]
    return requested in {_normalize_text(str(name)) for name in names if name}


def _google_component(components: list[dict], *types: str) -> str:
    for component in components:
        if any(item in component.get("types", []) for item in types):
            return component.get("long_name", "")
    return ""


def _google_geocode(query: str, state: str = "", district: str = "") -> dict | None:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not api_key:
        return None
    context = [query]
    if district and district != "All":
        context.append(district)
    if state and state != "All":
        context.append(state)
    context.append("India")
    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={"address": ", ".join(context), "components": "country:IN", "key": api_key},
        timeout=8,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "OK":
        return None
    requested = _requested_place_name(query)
    for result in payload.get("results", []):
        components = result.get("address_components", [])
        place_name = _google_component(components, "locality", "sublocality", "administrative_area_level_3")
        if requested != _normalize_text(place_name):
            continue
        location = result.get("geometry", {}).get("location", {})
        if "lat" not in location or "lng" not in location:
            continue
        resolved_state = _google_component(components, "administrative_area_level_1")
        resolved_district = _google_component(components, "administrative_area_level_2")
        return {
            "name": place_name,
            "state": resolved_state or state or "India",
            "district": resolved_district or district or "Mapped District",
            "village": place_name,
            "lat": float(location["lat"]),
            "lon": float(location["lng"]),
            "display_name": result.get("formatted_address", place_name),
            "provider": "google-maps-geocoding",
        }
    return None


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _stable_noise(*values: object) -> float:
    text = "|".join(str(value) for value in values)
    total = sum((index + 1) * ord(char) for index, char in enumerate(text))
    value = math.sin(total * 12.9898) * 43758.5453
    return value - math.floor(value)


def _distance_meters(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    radius_m = 6371000
    phi_a = math.radians(lat_a)
    phi_b = math.radians(lat_b)
    delta_phi = math.radians(lat_b - lat_a)
    delta_lambda = math.radians(lon_b - lon_a)
    hav = math.sin(delta_phi / 2) ** 2 + math.cos(phi_a) * math.cos(phi_b) * math.sin(delta_lambda / 2) ** 2
    return 2 * radius_m * math.atan2(math.sqrt(hav), math.sqrt(1 - hav))


def _now_label() -> str:
    return dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def estimate_breeding_likelihood(risk_score: float, days_persistent: int, ndwi: float) -> float:
    return round(_clamp(days_persistent / 21) * 35 + _clamp(ndwi) * 25 + _clamp(risk_score / 100) * 40, 1)


def estimate_mosquito_activity(risk_score: float, temperature: float, population_density: float) -> float:
    temperature_score = 1.0 if 24 <= temperature <= 34 else 0.55
    return round((0.55 * _clamp(risk_score / 100) + 0.25 * temperature_score + 0.20 * _clamp(population_density)) * 100, 1)


def classify_habitat(breeding_likelihood: float, mosquito_activity_index: float) -> str:
    if breeding_likelihood >= 75 and mosquito_activity_index >= 70:
        return "Probable breeding water body with high mosquito activity risk"
    if breeding_likelihood >= 55:
        return "Probable mosquito breeding water body"
    if mosquito_activity_index >= 55:
        return "Mosquito activity risk zone"
    return "Monitoring zone"


def _authority_for(state: str, district: str, village: str) -> tuple[str, str]:
    if district in {"Hyderabad", "Medchal-Malkajgiri", "Rangareddy"}:
        return "Municipality", "GHMC / Local Urban Body"
    if "Urban" in village:
        return "Municipality", f"{district} Municipal Sanitation Wing"
    return "Panchayat", f"{village} Panchayat Sanitation Team"


def _make_detection(state: str, district: str, base_lat: float, base_lon: float, template_index: int) -> Detection:
    zone_name, lat_offset, lon_offset, water_base, ndwi_base, pop_base, building_base, veg_base = ZONE_TEMPLATES[template_index]
    noise = _stable_noise(state, district, zone_name)
    lat = round(base_lat + lat_offset + (noise - 0.5) * 0.028, 5)
    lon = round(base_lon + lon_offset + (noise - 0.5) * 0.028, 5)
    village = f"{district} {zone_name}"
    water_persistence = _clamp(water_base + (noise - 0.45) * 0.20)
    ndwi = _clamp(ndwi_base + (noise - 0.45) * 0.18)
    population_density = _clamp(pop_base + (noise - 0.40) * 0.16)
    temperature = round(26.4 + (18.8 - lat) * 0.13 + noise * 2.1, 1)
    building_distance = _clamp(building_base + (0.5 - noise) * 0.12)
    vegetation = _clamp(veg_base + (noise - 0.45) * 0.15)
    days_persistent = max(2, int(round(4 + water_persistence * 17)))
    risk_input = RiskInput(water_persistence, ndwi, population_density, temperature, building_distance, vegetation)
    score = score_risk(risk_input)
    level = risk_level(score)
    breeding = estimate_breeding_likelihood(score, days_persistent, ndwi)
    activity = estimate_mosquito_activity(score, temperature, population_density)
    diseases = disease_suitability(score, temperature, population_density, 1 - building_distance)
    reasons = explain_detection(days_persistent, ndwi, temperature, population_density, level)
    reasons.insert(0, "Statewide AP/Telangana risk-map model estimate")
    reasons.append("Color meaning: green low, yellow medium, red high or critical")
    authority_type, authority_name = _authority_for(state, district, village)
    return Detection(
        id=f"{state[:2].upper()}-{district[:3].upper()}-{template_index + 1}-{int(noise * 10000)}",
        name=f"{district} {zone_name}",
        latitude=lat,
        longitude=lon,
        confidence=round(0.70 + noise * 0.22, 2),
        risk_score=score,
        risk_level=level,
        days_persistent=days_persistent,
        ndwi=round(ndwi, 2),
        temperature=temperature,
        population_density=round(population_density, 2),
        disease_index=diseases,
        breeding_likelihood=breeding,
        mosquito_activity_index=activity,
        habitat_type=classify_habitat(breeding, activity),
        reasons=reasons,
        recommendation=recommendation_for(level),
        state=state,
        district=district,
        village=village,
        authority_type=authority_type,
        authority_name=authority_name,
        last_updated=_now_label(),
    )


def build_statewide_detections() -> list[Detection]:
    detections = []
    for state, districts in DISTRICTS.items():
        for district, lat, lon in districts:
            for index in range(len(ZONE_TEMPLATES)):
                detections.append(_make_detection(state, district, lat, lon, index))
    return detections


def location_catalog() -> dict:
    return {
        "states": [
            {
                "name": state,
                "districts": [
                    {
                        "name": district,
                        "latitude": lat,
                        "longitude": lon,
                        "villages": [f"{district} {template[0]}" for template in ZONE_TEMPLATES],
                    }
                    for district, lat, lon in districts
                ],
            }
            for state, districts in DISTRICTS.items()
        ]
    }


def statewide_summary(items: list[dict]) -> dict:
    high = [item for item in items if item["risk_level"] in {"High", "Critical"}]
    medium = [item for item in items if item["risk_level"] == "Medium"]
    low = [item for item in items if item["risk_level"] == "Low"]
    return {
        "total_points": len(items),
        "red_zones": len(high),
        "yellow_zones": len(medium),
        "green_zones": len(low),
        "updated_at": _now_label(),
    }





@lru_cache(maxsize=256)
def _live_geocode(query: str, state: str = "", district: str = "") -> dict | None:
    if not query.strip():
        return None
    try:
        google_place = _google_geocode(query, state, district)
        if google_place:
            return google_place
    except Exception:
        pass
    contexts = []
    if district and district != "All" and state and state != "All":
        contexts.append(f"{query}, {district}, {state}, India")
    if state and state != "All":
        contexts.append(f"{query}, {state}, India")
    contexts.append(f"{query}, India")
    for search_text in contexts:
        try:
            response = requests.get(
                "https://nominatim.openstreetmap.org/search",
                params={"format": "jsonv2", "q": search_text, "limit": 10, "addressdetails": 1, "countrycodes": "in"},
                headers={"User-Agent": "MozzieSpotAI-MTech-Demo/1.0"},
                timeout=3,
            )
            if not response.ok:
                continue
            payload = response.json()
            if not payload:
                continue
            payload.sort(key=lambda item: _geocode_candidate_score(item, query, state, district), reverse=True)
            exact = [item for item in payload if _nominatim_exact_match(item, query)]
            if not exact:
                continue
            exact.sort(key=lambda item: _geocode_candidate_score(item, query, state, district), reverse=True)
            item = exact[0]
            display = item.get("display_name", "")
            address = item.get("address", {})
            state_name = address.get("state") or state or "India"
            district_name = address.get("state_district") or address.get("county") or district or "Mapped Search District"
            village_name = address.get("village") or address.get("town") or address.get("city") or address.get("municipality") or address.get("suburb") or address.get("hamlet") or query
            return {
                "name": item.get("name") or query,
                "state": state_name,
                "district": district_name.replace(" district", "").replace(" District", ""),
                "village": village_name,
                "lat": float(item["lat"]),
                "lon": float(item["lon"]),
                "display_name": display,
                "provider": "openstreetmap-nominatim",
            }
        except Exception:
            continue
    return None


def _apply_place_admin(detection: Detection, state: str, district: str, village: str) -> Detection:
    detection.state = state or detection.state
    detection.district = district or detection.district
    detection.village = village or detection.village
    detection.authority_type, detection.authority_name = _authority_for(detection.state, detection.district, detection.village)
    return detection


def _make_live_geocode_detection(place: dict, query: str) -> Detection:
    detection = analyze_statewide_spot(place["lat"], place["lon"], place.get("name") or query)
    detection.id = "LIVE-" + _normalize_text(query).replace(" ", "-").upper()[:50]
    detection.name = place.get("name") or query
    detection.latitude = place["lat"]
    detection.longitude = place["lon"]
    _apply_place_admin(
        detection,
        place.get("state") or detection.state,
        place.get("district") or detection.district,
        place.get("village") or detection.village,
    )
    detection.reasons.insert(0, f"Exact place search resolved with {place.get('provider', 'online geocoding')}")
    detection.last_updated = _now_label()
    return detection


def _nearby_generated_detections(latitude: float, longitude: float, limit: int = 12, radius_m: float = 15000) -> list[dict]:
    nearby = []
    for detection in build_statewide_detections():
        distance = _distance_meters(latitude, longitude, detection.latitude, detection.longitude)
        if distance <= radius_m:
            item = detection.to_dict()
            item["distance_m"] = round(distance)
            nearby.append(item)
    nearby.sort(key=lambda item: item["distance_m"])
    return nearby[:limit]


def _district_center(state: str = "", district: str = "") -> tuple[str, str, float, float]:
    if district and district != "All":
        for state_name, districts in DISTRICTS.items():
            for district_name, lat, lon in districts:
                if _normalize_text(district_name) == _normalize_text(district):
                    return state_name, district_name, lat, lon
    if state and state != "All" and state in STATE_CENTERS:
        lat, lon = STATE_CENTERS[state]
        return state, "Statewide Search Area", lat, lon
    lat, lon = STATE_CENTERS["Andhra Pradesh"]
    return "Andhra Pradesh", "Approximate Search Area", lat, lon


def _make_fallback_search_detection(query: str, state: str = "", district: str = "", village: str = "") -> Detection:
    state_name, district_name, base_lat, base_lon = _district_center(state, district)
    noise = _stable_noise("fallback", query, state_name, district_name, village)
    lat = round(base_lat + (noise - 0.5) * 0.08, 5)
    lon = round(base_lon + (_stable_noise(query, "lon") - 0.5) * 0.08, 5)
    display_name = query.strip() or village or "Searched place"
    detection = analyze_statewide_spot(lat, lon, display_name)
    detection.id = "SEARCH-" + _normalize_text(display_name).replace(" ", "-").upper()[:50]
    detection.name = display_name
    detection.latitude = lat
    detection.longitude = lon
    _apply_place_admin(detection, state_name, district_name, village if village and village != "All" else display_name)
    detection.reasons.insert(0, "Approximate place-name search marker generated from offline AP/Telangana map context")
    detection.reasons.append("For exact village accuracy, enter latitude and longitude or add this village to the gazetteer.")
    detection.last_updated = _now_label()
    return detection


def _make_place_detection(place: dict) -> Detection:
    base = analyze_statewide_spot(place["lat"], place["lon"], place["name"])
    base.id = "PLACE-" + _normalize_text(place["name"]).replace(" ", "-").upper()
    base.name = place["name"]
    base.latitude = place["lat"]
    base.longitude = place["lon"]
    _apply_place_admin(base, place["state"], place["district"], place["village"])
    base.reasons.insert(0, "Matched by place-name search")
    base.last_updated = _now_label()
    return base



def geocode_place(query: str, state: str = "", district: str = "") -> dict:
    cleaned_query = query.strip()
    if not cleaned_query:
        return {"found": False, "message": "Enter a place name"}

    for place in PLACE_GAZETTEER:
        if state and state != "All" and place["state"] != state:
            continue
        if district and district != "All" and place["district"] != district:
            continue
        if _place_matches(place, cleaned_query):
            detection = _make_place_detection(place).to_dict()
            detection["search_match"] = True
            detection["exact_place_match"] = True
            detection["geocode_source"] = "offline-gazetteer"
            return {"found": True, "detection": detection, "source": "offline-gazetteer"}

    live_place = _live_geocode(cleaned_query, state, district)
    if live_place:
        detection = _make_live_geocode_detection(live_place, cleaned_query).to_dict()
        detection["search_match"] = True
        detection["exact_place_match"] = True
        detection["zoom_to_place"] = True
        detection["geocode_source"] = live_place.get("provider", "openstreetmap-nominatim")
        return {
            "found": True,
            "detection": detection,
            "source": live_place.get("provider", "openstreetmap-nominatim"),
            "display_name": live_place.get("display_name"),
        }

    return {
        "found": False,
        "message": "No exact Indian village, town, or city match was found. Add district and state, for example: Rampur, Uttar Pradesh.",
    }



def _best_gazetteer_match(query: str, state: str = "", district: str = "", village: str = "") -> dict | None:
    if not query.strip():
        return None
    exact_query = _normalize_text(query)
    candidates = []
    for place in PLACE_GAZETTEER:
        if state and state != "All" and place["state"] != state:
            continue
        if district and district != "All" and place["district"] != district:
            continue
        if village and village != "All" and place["village"] != village:
            continue
        names = [place["name"], place["village"], *place.get("aliases", [])]
        normalized_names = [_normalize_text(name) for name in names]
        if exact_query in normalized_names:
            return place
        if all(token in " ".join(normalized_names) for token in exact_query.split()):
            candidates.append((3, place))
        elif _place_matches(place, query):
            candidates.append((2, place))
    if candidates:
        candidates.sort(key=lambda item: item[0], reverse=True)
        return candidates[0][1]
    return None


def _search_area_risk_zones(center: Detection, limit: int = 8) -> list[dict]:
    templates = [
        ("Nearby drain risk", 0.0045, 0.0052),
        ("Nearby tank risk", -0.0062, 0.0048),
        ("Low-lying street water risk", 0.0058, -0.0066),
        ("Canal-side mosquito risk", -0.0048, -0.0062),
        ("Residential water storage risk", 0.0025, -0.0086),
        ("Open plot stagnant-water risk", -0.0080, 0.0019),
        ("Agricultural field pooling risk", 0.0090, 0.0028),
        ("Roadside drainage risk", -0.0022, -0.0094),
    ]
    zones = []
    for index, (label, lat_offset, lon_offset) in enumerate(templates[:limit]):
        lat = round(center.latitude + lat_offset, 5)
        lon = round(center.longitude + lon_offset, 5)
        zone = analyze_statewide_spot(lat, lon, f"{label} near {center.name}")
        zone.id = f"AROUND-{center.id}-{index + 1}"
        _apply_place_admin(zone, center.state, center.district, center.village)
        zone.reasons.insert(0, "Risk zone generated around searched place")
        item = zone.to_dict()
        item["near_search_area"] = True
        item["distance_m"] = round(_distance_meters(center.latitude, center.longitude, lat, lon))
        zones.append(item)
    zones.sort(key=lambda item: item["risk_score"], reverse=True)
    return zones


def filter_detections(state: str = "", district: str = "", village: str = "", query: str = "", minimum: str = "Low") -> list[dict]:
    order = {"Low": 0, "Medium": 1, "High": 2, "Critical": 3}
    minimum_rank = order.get(minimum, 0)
    results = []
    seen_ids = set()
    search_center = None

    if query:
        local_place = _best_gazetteer_match(query, state, district, village)
        if local_place:
            search_center = _make_place_detection(local_place)
            center_item = search_center.to_dict()
            center_item["search_match"] = True
            center_item["exact_place_match"] = True
            center_item["gazetteer_place"] = True
            center_item["zoom_to_place"] = True
            results.append(center_item)
            seen_ids.add(center_item["id"])
        else:
            live_place = _live_geocode(query, state, district)
            if live_place:
                search_center = _make_live_geocode_detection(live_place, query)
                center_item = search_center.to_dict()
                center_item["search_match"] = True
                center_item["exact_place_match"] = True
                center_item["geocoded_place"] = True
                center_item["zoom_to_place"] = True
                results.append(center_item)
                seen_ids.add(center_item["id"])

        if search_center is None:
            search_center = _make_fallback_search_detection(query, state, district, village)
            center_item = search_center.to_dict()
            center_item["search_match"] = True
            center_item["approximate_place"] = True
            center_item["zoom_to_place"] = True
            results.append(center_item)
            seen_ids.add(center_item["id"])

        for nearby in _search_area_risk_zones(search_center):
            if order[nearby["risk_level"]] >= minimum_rank and nearby["id"] not in seen_ids:
                results.append(nearby)
                seen_ids.add(nearby["id"])

        for nearby in _nearby_generated_detections(search_center.latitude, search_center.longitude, limit=10, radius_m=30000):
            if order[nearby["risk_level"]] >= minimum_rank and nearby["id"] not in seen_ids:
                nearby["near_search_area"] = True
                results.append(nearby)
                seen_ids.add(nearby["id"])

        return sorted(
            results,
            key=lambda item: (
                3 if item.get("zoom_to_place") else 2 if item.get("near_search_area") else 1 if item.get("search_match") else 0,
                item.get("risk_score", 0),
                item.get("breeding_likelihood", 0),
            ),
            reverse=True,
        )

    for detection in build_statewide_detections():
        if state and state != "All" and detection.state != state:
            continue
        if district and district != "All" and detection.district != district:
            continue
        if village and village != "All" and detection.village != village:
            continue
        if order[detection.risk_level] < minimum_rank:
            continue
        item = detection.to_dict()
        results.append(item)

    return sorted(results, key=lambda item: (item["risk_score"], item["breeding_likelihood"]), reverse=True)


def analyze_statewide_spot(latitude: float, longitude: float, name: str | None = None) -> Detection:
    detections = build_statewide_detections()
    nearest = min(detections, key=lambda item: _distance_meters(latitude, longitude, item.latitude, item.longitude))
    nearest_distance = _distance_meters(latitude, longitude, nearest.latitude, nearest.longitude)
    influence = _clamp(1 - nearest_distance / 5000)
    noise = _stable_noise(latitude, longitude, nearest.id)
    has_nearby_water = nearest_distance <= 1500
    water_persistence = _clamp(0.15 + nearest.days_persistent / 21 * 0.70 * influence + noise * 0.10) if has_nearby_water else 0.0
    ndwi = _clamp(0.16 + nearest.ndwi * 0.74 * influence + noise * 0.08) if has_nearby_water else 0.0
    population_density = _clamp(0.25 + nearest.population_density * 0.70 * influence + noise * 0.10)
    temperature = round(nearest.temperature + (noise - 0.5) * 1.6, 1)
    building_distance = _clamp(0.68 - (nearest.population_density * 0.45 * influence) + noise * 0.08)
    vegetation = _clamp(0.22 + noise * 0.44)
    days_persistent = max(1, int(round(2 + water_persistence * 18))) if has_nearby_water else 0
    risk_input = RiskInput(water_persistence, ndwi, population_density, temperature, building_distance, vegetation)
    score = score_risk(risk_input)
    level = risk_level(score)
    breeding = estimate_breeding_likelihood(score, days_persistent, ndwi)
    activity = estimate_mosquito_activity(score, temperature, population_density)
    diseases = disease_suitability(score, temperature, population_density, 1 - building_distance)
    reasons = explain_detection(days_persistent, ndwi, temperature, population_density, level)
    reasons.insert(0, "Prediction generated for selected latitude and longitude")
    if has_nearby_water:
        reasons.append(f"Nearest mapped waterbody evidence is {round(nearest_distance)} m away in {nearest.district}")
    else:
        level = "Low"
        score = 0.0
        breeding = 0.0
        activity = 0.0
        diseases = {key: 0.0 for key in diseases}
        reasons = ["No mapped waterbody evidence was found within 1.5 km; land is not classified as a mosquito waterbody risk."]
    authority_type, authority_name = _authority_for(nearest.state, nearest.district, nearest.village)
    return Detection(
        id=f"SPOT-{abs(hash((round(latitude, 5), round(longitude, 5)))) % 100000}",
        name=name or f"Selected Spot {latitude:.4f}, {longitude:.4f}",
        latitude=latitude,
        longitude=longitude,
        confidence=round(0.62 + influence * 0.30, 2),
        risk_score=score,
        risk_level=level,
        days_persistent=days_persistent,
        ndwi=round(ndwi, 2),
        temperature=temperature,
        population_density=round(population_density, 2),
        disease_index=diseases,
        breeding_likelihood=breeding,
        mosquito_activity_index=activity,
        habitat_type=classify_habitat(breeding, activity) if has_nearby_water else "No waterbody evidence",
        reasons=reasons,
        recommendation=recommendation_for(level),
        state=nearest.state,
        district=nearest.district,
        village=nearest.village,
        authority_type=authority_type,
        authority_name=authority_name,
        last_updated=_now_label(),
    )


def nearby_risk(latitude: float, longitude: float, radius_m: float = 2500) -> dict:
    detections = []
    for detection in build_statewide_detections():
        distance = _distance_meters(latitude, longitude, detection.latitude, detection.longitude)
        if distance <= radius_m:
            item = detection.to_dict()
            item["distance_m"] = round(distance)
            detections.append(item)
    detections.sort(key=lambda item: item["distance_m"])
    return {
        "current_spot": analyze_statewide_spot(latitude, longitude, "Live walking location").to_dict(),
        "nearby": detections[:25],
        "radius_m": radius_m,
        "updated_at": _now_label(),
    }
