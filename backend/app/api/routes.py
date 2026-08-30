import datetime as dt
from pathlib import Path
from urllib.parse import quote

import jwt
from flask import Blueprint, Response, current_app, jsonify, request, send_file

from app.services.advanced_service import (
    MODULES,
    admin_roles,
    analytics_summary,
    detections_csv,
    detections_excel,
    detections_geojson,
    detections_shapefile_zip,
    enhance_detection,
    satellite_layers_payload,
    telegram_status,
)
from app.services.alert_service import send_email_alert, send_telegram_alert
from app.services.detection_service import build_detections, dashboard_summary, search_mosquito_habitats
from app.services.region_service import (
    analyze_statewide_spot,
    filter_detections,
    geocode_place,
    location_catalog,
    nearby_risk,
    statewide_summary,
)
from app.services.report_service import build_weekly_pdf
from app.services.satellite_service import SatelliteService
from app.services.validation_service import calibration_bins, segmentation_metrics, threshold_curves, validation_status
from app.satellite.config import OUTPUT_DIR

api = Blueprint("api", __name__)


def _statewide_detection_dicts() -> list[dict]:
    return filter_detections(
        state="All",
        district="All",
        village="All",
        query="",
        minimum="Low",
    )


def _enhance_many(items: list[dict]) -> list[dict]:
    return [enhance_detection(item) for item in items]


def _waterbody_only(items: list[dict]) -> list[dict]:
    return [item for item in _enhance_many(items) if item.get("is_waterbody")]


@api.get("/health")
def health():
    return {"status": "ok", "service": "mozziespot-ai"}


@api.post("/auth/login")
def login():
    payload = request.get_json(force=True)
    if payload.get("email") != "officer@mozziespot.ai" or payload.get("password") != "demo123":
        return {"message": "Invalid credentials"}, 401
    token = jwt.encode(
        {"sub": payload["email"], "role": "Health Officer", "exp": dt.datetime.utcnow() + dt.timedelta(hours=8)},
        current_app.config["JWT_SECRET"],
        algorithm="HS256",
    )
    return {"token": token, "user": {"email": payload["email"], "role": "Health Officer"}}


@api.get("/dashboard")
def dashboard():
    return jsonify(dashboard_summary())


@api.get("/detections")
def detections():
    return jsonify(_enhance_many([d.to_dict() for d in build_detections()]))


@api.get("/locations")
def locations():
    return jsonify(location_catalog())


@api.post("/geocode/place")
def geocode_selected_place():
    payload = request.get_json(force=True)
    query = payload.get("query", "")
    state = payload.get("state", "All")
    district = payload.get("district", "All")
    result = geocode_place(query=query, state=state, district=district)
    if result.get("found") and result.get("detection"):
        result["detection"] = enhance_detection(result["detection"])
    status_code = 200 if result.get("found") else 404
    return jsonify(result), status_code


@api.get("/state-risk")
def state_risk():
    results = filter_detections(
        state=request.args.get("state", "All"),
        district=request.args.get("district", "All"),
        village=request.args.get("village", "All"),
        query=request.args.get("q", ""),
        minimum=request.args.get("minimum", "Low"),
    )
    enhanced = _waterbody_only(results)
    return jsonify(
        {
            "status": "completed",
            "note": "Map colors show probable breeding waterbody and mosquito-activity risk. Satellite maps cannot directly see eggs or adult mosquitoes.",
            "summary": statewide_summary(enhanced),
            "results": enhanced,
        }
    )


@api.get("/advanced/modules")
def advanced_modules():
    return jsonify({"status": "completed", "modules": MODULES})


@api.get("/validation/status")
def get_validation_status():
    backend_root = Path(__file__).resolve().parents[2]
    return jsonify(validation_status(backend_root))


@api.post("/validation/evaluate")
def evaluate_segmentation():
    payload = request.get_json(force=True)
    try:
        actual = payload["actual"]
        probabilities = payload["probabilities"]
        threshold = float(payload.get("threshold", 0.5))
        predicted = [1 if float(value) >= threshold else 0 for value in probabilities]
        return jsonify(
            {
                "status": "completed",
                "threshold": threshold,
                "metrics": segmentation_metrics(actual, predicted),
                "curves": threshold_curves(actual, probabilities),
                "calibration": calibration_bins(actual, probabilities),
            }
        )
    except (KeyError, TypeError, ValueError) as error:
        return {"message": str(error)}, 400


@api.get("/analytics")
def analytics():
    return jsonify({"status": "completed", **analytics_summary(_statewide_detection_dicts())})


@api.get("/admin/roles")
def roles():
    return jsonify(admin_roles())


@api.get("/satellite/metadata")
def satellite_metadata():
    result = SatelliteService().search({})
    scene = result.get("selected_scene", {})
    return jsonify(
        {
            "id": scene.get("id", "Sentinel-2 L2A"),
            "date": scene.get("datetime"),
            "cloud_cover": scene.get("cloud_cover"),
            "bbox": scene.get("bbox") or result.get("bbox"),
            "source": result.get("source"),
            "online": result.get("online"),
        }
    )


@api.post("/satellite/search")
def satellite_search():
    return jsonify(SatelliteService().search(request.get_json(silent=True) or {}))


@api.get("/satellite/download")
def satellite_download():
    payload = {
        "start_date": request.args.get("start_date"),
        "end_date": request.args.get("end_date"),
        "cloud_cover": request.args.get("cloud_cover", 15),
    }
    return jsonify(SatelliteService().download(payload))


@api.post("/satellite/download")
def satellite_download_post():
    return jsonify(SatelliteService().download(request.get_json(silent=True) or {}))


@api.post("/satellite/process")
def satellite_process():
    return jsonify(SatelliteService().process(payload=request.get_json(silent=True) or {}))


@api.post("/satellite/water-detection")
def detect_water():
    result = SatelliteService().process(payload=request.get_json(silent=True) or {})
    return jsonify({"status": "success", "output": result["outputs"]["water"], "details": result})


@api.get("/satellite/ndwi/statistics")
def ndwi_statistics():
    detections_payload = _statewide_detection_dicts()
    water_pixels = int(sum(item.get("ndwi", 0) * 1200 for item in detections_payload))
    land_pixels = max(1, len(detections_payload) * 4200)
    return jsonify(
        {
            "water_pixels": water_pixels,
            "land_pixels": land_pixels,
            "water_percentage": round((water_pixels / (water_pixels + land_pixels)) * 100, 2),
        }
    )


@api.get("/satellite/heatmap")
def satellite_heatmap():
    points = [
        {
            "latitude": item["latitude"],
            "longitude": item["longitude"],
            "intensity": round(item["risk_score"] / 100, 2),
        }
        for item in _statewide_detection_dicts()
    ]
    return jsonify({"status": "success", "points": points})


@api.get("/satellite/layers")
def satellite_layers():
    return jsonify(satellite_layers_payload())


@api.get("/satellite/output/<scene_id>/<filename>")
def download_satellite_output(scene_id: str, filename: str):
    """Serve only raster products generated by this application."""
    allowed = {"rgb_preview.tif", "rgb_preview.png", "ndwi.tif", "mndwi.tif", "ndvi.tif", "water_mask.tif", "probable_waterbodies.geojson"}
    if scene_id != Path(scene_id).name or filename not in allowed:
        return {"message": "Output file not found"}, 404
    path = OUTPUT_DIR / scene_id / filename
    if not path.is_file():
        return {"message": "Output file not ready. Download and process the selected Sentinel-2 scene first."}, 404
    return send_file(path, as_attachment=path.suffix != ".png", download_name=filename)


@api.post("/analyze")
def analyze():
    detections_payload = _enhance_many([d.to_dict() for d in build_detections()])
    return jsonify({"status": "completed", "scene_id": request.form.get("scene_id", "demo-scene"), "detections": detections_payload})


@api.post("/analyze/spot")
def analyze_selected_spot():
    payload = request.get_json(force=True)
    try:
        latitude = float(payload["latitude"])
        longitude = float(payload["longitude"])
    except (KeyError, TypeError, ValueError):
        return {"message": "latitude and longitude are required numbers"}, 400
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        return {"message": "latitude or longitude is outside valid range"}, 400
    detection = enhance_detection(analyze_statewide_spot(latitude, longitude, payload.get("name")).to_dict())
    return jsonify({"status": "completed", "detection": detection})


@api.post("/nearby-risk")
def walking_nearby_risk():
    payload = request.get_json(force=True)
    try:
        latitude = float(payload["latitude"])
        longitude = float(payload["longitude"])
        radius_m = float(payload.get("radius_m", 2500))
    except (KeyError, TypeError, ValueError):
        return {"message": "latitude and longitude are required numbers"}, 400
    result = nearby_risk(latitude, longitude, radius_m)
    result["current_spot"] = enhance_detection(result["current_spot"])
    result["nearby"] = _enhance_many(result["nearby"])
    return jsonify({"status": "completed", **result})


@api.get("/search/mosquito-habitats")
def mosquito_habitat_search():
    query = request.args.get("q", "")
    minimum = request.args.get("minimum", "Medium")
    return jsonify(
        {
            "status": "completed",
            "note": "Satellite data estimates probable breeding habitats and mosquito activity risk; it does not directly see eggs or adult mosquitoes.",
            "results": _enhance_many(search_mosquito_habitats(query=query, minimum=minimum)),
        }
    )


def _authority_message(detection: dict) -> str:
    diseases = detection.get("advanced_disease_index") or detection.get("disease_index", {})
    return (
        "MozzieSpot AI Cleaning Alert\n"
        f"Authority: {detection.get('authority_name', 'Local sanitation authority')}\n"
        f"Area: {detection['name']}\n"
        f"State/District: {detection.get('state')} / {detection.get('district')}\n"
        f"Village/Ward: {detection.get('village')}\n"
        f"Risk: {detection.get('mosquito_risk_level', detection['risk_level'])} ({detection.get('mosquito_risk_score', detection['risk_score'])})\n"
        f"Water type: {detection.get('water_type', detection.get('habitat_type'))}\n"
        f"Breeding likelihood: {detection.get('breeding_likelihood')}%\n"
        f"Mosquito activity: {detection.get('mosquito_activity_index')}%\n"
        f"Diseases: Dengue {diseases.get('dengue')}%, Malaria {diseases.get('malaria')}%, Chikungunya {diseases.get('chikungunya')}%, JE {diseases.get('japanese_encephalitis', 'NA')}%\n"
        f"Location: https://www.google.com/maps?q={detection['latitude']},{detection['longitude']}\n"
        f"Action: {detection['recommendation']}"
    )


@api.post("/alerts/send")
def send_alert():
    payload = request.get_json(force=True)
    detection = payload.get("detection")
    if not detection:
        return {"message": "detection is required"}, 400
    checked = enhance_detection(detection)
    if not checked.get("is_waterbody"):
        return {"message": "Alert not sent: this location has no probable waterbody evidence."}, 422
    message = _authority_message(checked)
    telegram = send_telegram_alert(message)
    email = {"sent": False, "reason": "email not requested"}
    if payload.get("email"):
        email = send_email_alert(payload["email"], "MozzieSpot AI Public Health Alert", message)
    whatsapp_number = payload.get("whatsapp_number", "")
    whatsapp_url = "https://wa.me/" + whatsapp_number + "?text=" + quote(message) if whatsapp_number else "https://wa.me/?text=" + quote(message)
    map_url = f"https://www.google.com/maps?q={detection['latitude']},{detection['longitude']}"
    telegram_url = "https://t.me/share/url?url=" + quote(map_url) + "&text=" + quote(message)
    return {"telegram": telegram, "email": email, "whatsapp_url": whatsapp_url, "telegram_url": telegram_url, "message": message}


@api.get("/telegram/status")
def get_telegram_status():
    return jsonify(telegram_status())


@api.get("/reports/weekly")
def weekly_report():
    pdf = build_weekly_pdf(dashboard_summary(), _statewide_detection_dicts())
    return Response(pdf, mimetype="application/pdf", headers={"Content-Disposition": "attachment; filename=mozziespot-weekly-report.pdf"})


@api.get("/reports/daily")
def daily_report():
    pdf = build_weekly_pdf(dashboard_summary(), _statewide_detection_dicts())
    return Response(pdf, mimetype="application/pdf", headers={"Content-Disposition": "attachment; filename=mozziespot-daily-report.pdf"})


@api.get("/export/csv")
def export_csv():
    body = detections_csv(_statewide_detection_dicts())
    return Response(body, mimetype="text/csv", headers={"Content-Disposition": "attachment; filename=mozziespot-risk-zones.csv"})


@api.get("/export/excel")
def export_excel():
    body = detections_excel(_statewide_detection_dicts())
    return Response(
        body,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=mozziespot-risk-zones.xlsx"},
    )


@api.get("/export/geojson")
def export_geojson():
    return jsonify(detections_geojson(_statewide_detection_dicts()))


@api.get("/export/shapefile")
def export_shapefile():
    body = detections_shapefile_zip(_statewide_detection_dicts())
    return Response(body, mimetype="application/zip", headers={"Content-Disposition": "attachment; filename=mozziespot-risk-zones-shapefile.zip"})
