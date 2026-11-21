import json
from pathlib import Path
from app.extensions import db
from app.models import Category, Question, AcceptedAnswer, AnswerAlias
from app.services.answer_validator import normalize_answer

def seed_questions():
    path = Path(__file__).resolve().parent.parent / "seed" / "questions.json"
    for item in json.loads(path.read_text(encoding="utf-8")):
        cdata = item["category"]
        category = Category.query.filter_by(slug=cdata["slug"]).first()
        if category is None:
            category = Category(slug=cdata["slug"], name=cdata["name"], description=cdata.get("description"))
            db.session.add(category)
            db.session.flush()
        question = Question.query.filter_by(slug=item["slug"]).first()
        if question is None:
            question = Question(slug=item["slug"], prompt=item["prompt"], difficulty=item.get("difficulty", 1), status="approved", category=category)
            db.session.add(question)
            db.session.flush()
        for a in item.get("answers", []):
            answer = AcceptedAnswer.query.filter_by(question_id=question.id, canonical=a["canonical"]).first()
            if answer is None:
                answer = AcceptedAnswer(question=question, canonical=a["canonical"], normalized=normalize_answer(a["canonical"]), rarity_tier=a["rarity_tier"], points=a["points"], explanation=a.get("explanation"), source_url=a.get("source_url"), license_name=a.get("license_name"))
                db.session.add(answer)
                db.session.flush()
            for alias in a.get("aliases", []):
                norm = normalize_answer(alias)
                if not AnswerAlias.query.filter_by(normalized=norm).first():
                    db.session.add(AnswerAlias(answer=answer, alias=alias, normalized=norm))
    db.session.commit()
