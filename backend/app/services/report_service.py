from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def build_weekly_pdf(summary: dict, detections: list[dict]) -> bytes:
    buffer = BytesIO()
    page = canvas.Canvas(buffer, pagesize=A4)
    page.setTitle("MozzieSpot AI Weekly Risk Report")
    page.setFont("Helvetica-Bold", 16)
    page.drawString(50, 800, "MozzieSpot AI Weekly Risk Report")
    page.setFont("Helvetica", 10)
    page.drawString(50, 775, f"Water bodies: {summary['water_bodies']} | High-risk zones: {summary['high_risk_zones']} | Disease index: {summary['disease_index']}")
    y = 740
    for detection in detections[:12]:
        page.setFont("Helvetica-Bold", 10)
        page.drawString(50, y, f"{detection['name']} - {detection['risk_level']} ({detection['risk_score']})")
        y -= 14
        page.setFont("Helvetica", 9)
        page.drawString(65, y, detection["recommendation"][:100])
        y -= 24
        if y < 80:
            page.showPage()
            y = 790
    page.save()
    return buffer.getvalue()

