from flask import Blueprint, jsonify
from app.models import Question
bp = Blueprint("questions", __name__)
@bp.get("/questions")
def list_questions():
    rows = Question.query.filter_by(status="approved").order_by(Question.id).all()
    return jsonify([{"id": q.id, "slug": q.slug, "prompt": q.prompt, "difficulty": q.difficulty, "category": q.category.name} for q in rows])
