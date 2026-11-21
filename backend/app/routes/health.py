from flask import Blueprint, jsonify
from sqlalchemy import text
from app.extensions import db
bp = Blueprint("health", __name__)
@bp.get("/health")
def health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "database": "connected"})
    except Exception:
        db.session.rollback()
        return jsonify({"status": "degraded", "database": "unavailable"}), 503
