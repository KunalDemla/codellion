import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify
from sqlalchemy.exc import IntegrityError
from .config import Config
from .extensions import db, migrate, cors

def create_app(test_config=None):
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    if app.config["APP_ENV"] == "production" and (
        app.config["SECRET_KEY"] == "dev-only-change-me" or len(app.config["SECRET_KEY"]) < 32
    ):
        raise RuntimeError("Production requires a SECRET_KEY with at least 32 characters.")

    db.init_app(app)
    migrate.init_app(app, db, compare_type=True)
    origins = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173").split(",")
    cors.init_app(app, resources={r"/api/*": {"origins": [x.strip() for x in origins]}})

    from . import models  # noqa: F401
    from .routes.health import bp as health_bp
    from .routes.games import bp as games_bp
    from .routes.questions import bp as questions_bp
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(games_bp, url_prefix="/api")
    app.register_blueprint(questions_bp, url_prefix="/api")

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(_error):
        db.session.rollback()
        return jsonify({"error": {"code": "conflict", "message": "This action conflicts with existing game data."}}), 409

    @app.errorhandler(404)
    def handle_not_found(_error):
        return jsonify({"error": {"code": "not_found", "message": "Resource not found."}}), 404

    return app
