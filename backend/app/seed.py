import json
from pathlib import Path
from app.extensions import db
from app.models import Category, Question, AcceptedAnswer, AnswerAlias, GameSubmission
from app.services.answer_validator import normalize_answer

TIER_POINTS = {1: 10, 2: 15, 3: 30, 4: 60, 5: 85, 6: 100}

def validate_seed(items):
    if not isinstance(items, list) or len(items) < 7:
        raise ValueError("Seed data must contain at least seven questions.")
    for item in items:
        answers = item.get("answers", [])
        if len(answers) != 6:
            raise ValueError(f"{item.get('slug')}: each question must have six scored answers.")
        if {answer.get("rarity_tier") for answer in answers} != set(TIER_POINTS):
            raise ValueError(f"{item.get('slug')}: tiers 1 through 6 must each appear once.")
        seen = set()
        for answer in answers:
            tier = answer["rarity_tier"]
            if answer.get("points") != TIER_POINTS[tier]:
                raise ValueError(f"{item.get('slug')}: tier {tier} must score {TIER_POINTS[tier]} points.")
            for text in [answer["canonical"], *answer.get("aliases", [])]:
                normalized = normalize_answer(text)
                if not normalized or normalized in seen:
                    raise ValueError(f"{item.get('slug')}: duplicate or empty canonical answer/alias {text!r}.")
                seen.add(normalized)

def seed_questions():
    path = Path(__file__).resolve().parents[1] / "seed" / "questions.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    validate_seed(items)
    for item in items:
        cdata = item["category"]
        category = Category.query.filter_by(slug=cdata["slug"]).first()
        if category is None:
            category = Category(slug=cdata["slug"], name=cdata["name"], description=cdata.get("description"))
            db.session.add(category)
            db.session.flush()
        else:
            category.name = cdata["name"]
        question = Question.query.filter_by(slug=item["slug"]).first()
        if question is None:
            question = Question(slug=item["slug"], prompt=item["prompt"], category=category)
            db.session.add(question)
        question.prompt = item["prompt"]
        question.difficulty = item.get("difficulty", 1)
        question.status = item.get("status", "approved")
        question.category = category
        db.session.flush()
        current_answer_norms = {normalize_answer(a["canonical"]) for a in item.get("answers", [])}
        for a in item.get("answers", []):
            canonical_norm = normalize_answer(a["canonical"])
            answer = AcceptedAnswer.query.filter_by(question_id=question.id, normalized=canonical_norm).first()
            if answer is None:
                answer = AcceptedAnswer(question=question, canonical=a["canonical"], normalized=canonical_norm,
                    rarity_tier=a["rarity_tier"], points=a["points"])
                db.session.add(answer)
            answer.canonical = a["canonical"]
            answer.rarity_tier = a["rarity_tier"]
            answer.points = a["points"]
            answer.explanation = a.get("explanation")
            answer.source_url = a.get("source_url")
            answer.license_name = a.get("license_name")
            db.session.flush()
            aliases = a.get("aliases", [])
            alias_norms = {normalize_answer(text) for text in aliases}
            for old_alias in list(answer.aliases):
                if old_alias.normalized not in alias_norms:
                    db.session.delete(old_alias)
            for alias_text in aliases:
                alias_norm = normalize_answer(alias_text)
                existing = AnswerAlias.query.filter_by(answer_id=answer.id, normalized=alias_norm).first()
                if existing is None:
                    db.session.add(AnswerAlias(answer=answer, alias=alias_text, normalized=alias_norm))
                else:
                    existing.alias = alias_text
        # Retire seed answers removed from the curated file when no historical
        # submission depends on them. Keep referenced rows to preserve old runs.
        for stale in list(AcceptedAnswer.query.filter_by(question_id=question.id).all()):
            if stale.normalized not in current_answer_norms and not GameSubmission.query.filter_by(accepted_answer_id=stale.id).first():
                db.session.delete(stale)
    db.session.commit()
