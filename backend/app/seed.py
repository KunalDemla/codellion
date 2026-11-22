import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models import (
    AcceptedAnswer, AnswerAlias, Category, DailyChallenge, DailyChallengeQuestion, Game, GameSubmission, Question,
)
from app.services.answer_validator import normalize_answer

SEED_DIR = Path(__file__).resolve().parents[1] / "seed"
BANK_FILES = {"starter": "questions.json", "curated": "curated_questions.json"}
TIER_POINTS = {1: 10, 2: 15, 3: 30, 4: 60, 5: 85, 6: 100}


def validate_seed(items, *, curated=False):
    if not isinstance(items, list) or len(items) < 7:
        raise ValueError("Seed data must contain at least seven questions.")
    slugs = set()
    for item in items:
        slug = item["slug"]
        if len(slug) > 120 or slug in slugs:
            raise ValueError(f"Invalid or duplicate question slug: {slug}.")
        slugs.add(slug)
        answers = item.get("answers", [])
        tiers = Counter(answer.get("rarity_tier") for answer in answers)
        if set(tiers) != set(TIER_POINTS) or tiers[6] != 1:
            raise ValueError(f"{slug}: all six tiers are required, with exactly one Root Key.")
        if curated and (not item.get("scope") or any(tiers[tier] < 2 for tier in range(1, 6))):
            raise ValueError(f"{slug}: curated questions require a defined scope and multiple answers in the first five tiers.")
        seen = set()
        for answer in answers:
            tier = answer["rarity_tier"]
            if answer.get("points") != TIER_POINTS[tier]:
                raise ValueError(f"{slug}: tier {tier} must score {TIER_POINTS[tier]} points.")
            if curated and (urlsplit(answer.get("source_url", "")).scheme != "https" or not answer.get("license_name")):
                raise ValueError(f"{slug}: answer provenance is required.")
            for text in [answer["canonical"], *answer.get("aliases", [])]:
                normalized = normalize_answer(text, item.get("case_sensitive", False))
                if not normalized or normalized in seen or len(text) > 256 or len(normalized) > 256:
                    raise ValueError(f"{slug}: duplicate, empty, or oversized canonical answer/alias {text!r}.")
                seen.add(normalized)


def _sync_aliases(answer, aliases, case_sensitive):
    existing = {alias.normalized: alias for alias in answer.aliases}
    desired = {normalize_answer(text, case_sensitive): text for text in aliases}
    if desired == {key: alias.alias for key, alias in existing.items()}:
        return
    updated = []
    for key, text in desired.items():
        alias = existing.get(key) or AnswerAlias(normalized=key)
        alias.alias = text
        updated.append(alias)
    answer.aliases[:] = updated


def _sync_live_aliases(question, item):
    if (question.prompt != item["prompt"]
            or question.scope != item.get("scope")
            or question.case_sensitive != item.get("case_sensitive", False)):
        return
    answers = {answer.canonical: answer for answer in question.answers if answer.is_active}
    entries = {entry["canonical"]: entry for entry in item["answers"]}
    if answers.keys() != entries.keys() or any(
        (answer.rarity_tier, answer.points) != (entries[name]["rarity_tier"], entries[name]["points"])
        for name, answer in answers.items()
    ):
        return
    for name, answer in answers.items():
        _sync_aliases(answer, entries[name].get("aliases", []), question.case_sensitive)


def seed_questions(bank="curated"):
    items = json.loads((SEED_DIR / BANK_FILES[bank]).read_text(encoding="utf-8"))
    validate_seed(items, curated=bank == "curated")

    slugs = [item["slug"] for item in items]
    categories = {category.slug: category for category in Category.query.all()}
    existing = {q.slug: q for q in Question.query.filter(Question.slug.in_(slugs)).options(
        selectinload(Question.answers).selectinload(AcceptedAnswer.aliases),
    )}
    today = datetime.now(timezone.utc).date()
    live_ids = {question_id for (question_id,) in db.session.query(DailyChallengeQuestion.question_id)
        .filter_by(challenge_date=today)}
    used_answers = {answer_id for (answer_id,) in db.session.query(GameSubmission.accepted_answer_id).distinct()}

    for item in items:
        question = existing.get(item["slug"])
        if question and question.id in live_ids:
            _sync_live_aliases(question, item)
            continue
        cdata = item["category"]
        category = categories.get(cdata["slug"])
        if category is None:
            category = Category(slug=cdata["slug"], name=cdata["name"], description=cdata.get("description"))
            categories[category.slug] = category
            db.session.add(category)

        if question is None:
            question = Question(slug=item["slug"], category=category)
            db.session.add(question)
        question.prompt = item["prompt"]
        question.difficulty = item.get("difficulty", 1)
        question.scope = item.get("scope")
        question.case_sensitive = item.get("case_sensitive", False)
        question.allow_fuzzy = item.get("allow_fuzzy", True)
        question.status = item.get("status", "approved")
        question.category = category

        unmatched = {answer.normalized: answer for answer in question.answers}
        for entry in item["answers"]:
            normalized = normalize_answer(entry["canonical"], question.case_sensitive)
            answer = unmatched.pop(normalized, None)
            if answer is None:
                answer = AcceptedAnswer(normalized=normalized)
                question.answers.append(answer)
            answer.canonical = entry["canonical"]
            answer.rarity_tier = entry["rarity_tier"]
            answer.points = entry["points"]
            answer.is_active = True
            answer.explanation = entry.get("explanation")
            answer.source_url = entry.get("source_url")
            answer.license_name = entry.get("license_name")
            _sync_aliases(answer, entry.get("aliases", []), question.case_sensitive)
        for stale in unmatched.values():
            if stale.id in used_answers:
                stale.is_active = False
                stale.aliases.clear()
            else:
                question.answers.remove(stale)

    if bank == "curated":
        starter = json.loads((SEED_DIR / BANK_FILES["starter"]).read_text(encoding="utf-8"))
        starter_slugs = [item["slug"] for item in starter]
        managed = Question.slug.in_(starter_slugs) | Question.slug.like("curated-%")
        Question.query.filter(managed, Question.slug.not_in(slugs)).update({Question.status: "retired"})

        # Future API previews may have materialized lineups before publication.
        # Preserve the current daily, all past dates, and any lineup tied to a run.
        previews = DailyChallenge.query.filter(
            DailyChallenge.challenge_date > today,
            ~DailyChallenge.challenge_date.in_(db.select(Game.challenge_date)),
            DailyChallenge.questions.any(DailyChallengeQuestion.question.has(Question.status == "retired")),
        )
        for challenge in previews:
            db.session.delete(challenge)
    db.session.commit()
