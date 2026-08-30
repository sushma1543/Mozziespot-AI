import os


class Config:
    JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
    DATA_DIR = os.getenv("DATA_DIR", os.path.abspath(os.path.join(os.getcwd(), "..", "sample-data")))
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    ALERT_FROM_EMAIL = os.getenv("ALERT_FROM_EMAIL", "alerts@mozziespot.ai")
    GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
