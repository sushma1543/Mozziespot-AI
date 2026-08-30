import smtplib
from email.message import EmailMessage

import requests
from flask import current_app


def format_alert(detection: dict) -> str:
    return (
        f"MozzieSpot AI Alert\n"
        f"Area: {detection['name']}\n"
        f"Risk: {detection['risk_level']} ({detection['risk_score']})\n"
        f"Location: {detection['latitude']}, {detection['longitude']}\n"
        f"Action: {detection['recommendation']}"
    )


def send_telegram_alert(message: str) -> dict:
    token = current_app.config["TELEGRAM_BOT_TOKEN"]
    chat_id = current_app.config["TELEGRAM_CHAT_ID"]
    if not token or not chat_id:
        return {"sent": False, "reason": "Telegram credentials are not configured"}
    try:
        response = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )
        return {"sent": response.ok, "status_code": response.status_code}
    except Exception as exc:
        return {"sent": False, "reason": f"Telegram send failed: {exc}"}


def send_email_alert(to_email: str, subject: str, message: str) -> dict:
    host = current_app.config["SMTP_HOST"]
    user = current_app.config["SMTP_USER"]
    password = current_app.config["SMTP_PASSWORD"]
    if not host or not user or not password:
        return {"sent": False, "reason": "SMTP credentials are not configured"}
    email = EmailMessage()
    email["From"] = current_app.config["ALERT_FROM_EMAIL"]
    email["To"] = to_email
    email["Subject"] = subject
    email.set_content(message)
    with smtplib.SMTP(host, current_app.config["SMTP_PORT"]) as smtp:
        smtp.starttls()
        smtp.login(user, password)
        smtp.send_message(email)
    return {"sent": True}

