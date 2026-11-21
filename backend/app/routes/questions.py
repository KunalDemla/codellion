from flask import Blueprint, jsonify
from app.models import Category
bp = Blueprint("questions", __name__)

@bp.get("/categories")
def list_categories():
    rows = Category.query.order_by(Category.name).all()
    return jsonify([{"slug": c.slug, "name": c.name} for c in rows])
