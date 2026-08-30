from flask import Flask
from flask_cors import CORS

from app.api.routes import api
from app.core.config import Config


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    app.register_blueprint(api, url_prefix="/api")
    return app

