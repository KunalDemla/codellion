import os
from flask import Flask
from dotenv import load_dotenv
from .extensions import db, migrate, cors

def create_app():
    load_dotenv()
    from .config import Config

    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")}})
    from . import models
    from .routes import health, questions
    app.register_blueprint(health.bp, url_prefix="/api")
    app.register_blueprint(questions.bp, url_prefix="/api")
    return app
