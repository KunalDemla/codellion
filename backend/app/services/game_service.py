import hashlib
import re
import uuid
from difflib import SequenceMatcher
from datetime import date, datetime, time, timedelta, timezone
from sqlalchemy import and_, func, or_
from sqlalchemy.exc import IntegrityError
from flask import current_app
from app.extensions import db
from app.models import (Game, GameQuestion, GameSubmission, Question, AcceptedAnswer,
                        AnswerAlias, DailyChallenge, DailyChallengeQuestion)
from .answer_validator import normalize_answer
from .receipt import issue_receipt, verify_receipt

class GameError(Exception):
    def __init__(self, message, status_code=400, code="invalid_request"):
        self.message, self.status_code, self.code = message, status_code, code
        super().__init__(message)

def _parse_date(value):
    try:
        if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            raise ValueError
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise GameError("date must use YYYY-MM-DD format.", 400, "invalid_date")

def _uuid(value, field):
    try:
        return str(uuid.UUID(value))
    except (ValueError, TypeError, AttributeError):
        raise GameError(f"{field} must be a valid UUID.", 400, f"invalid_{field.lower()}")

def get_or_create_daily_challenge(challenge_date):
    challenge = db.session.get(DailyChallenge, challenge_date)
    if challenge:
        return challenge
    count = current_count()
    expected_points = current_app.config["RARITY_TIER_POINTS"]
    expected = {
        tier: and_(AcceptedAnswer.rarity_tier == tier, AcceptedAnswer.points == points)
        for tier, points in expected_points.items()
    }
    criteria = [func.count().filter(~or_(*expected.values())) == 0]
    for tier, valid in expected.items():
        entries = func.count().filter(valid)
        criteria.append(entries == 1 if tier == 6 else entries >= 1)
    available = (Question.query.filter_by(status="approved").join(Question.answers)
        .filter(AcceptedAnswer.is_active.is_(True))
        .group_by(Question.id).having(*criteria).all())
    if len(available) < count:
        raise GameError(f"Not enough approved questions with accepted answers. Need {count}, found {len(available)}.", 503, "question_bank_too_small")
    # Stable ordering means every player receives the same prompts in the same order.
    ranked = sorted(available, key=lambda q: hashlib.sha256(f"{challenge_date.isoformat()}:{q.slug}".encode()).hexdigest())
    ordered, extras, categories = [], [], set()
    for question in ranked:
        if question.category_id in categories:
            extras.append(question)
        else:
            ordered.append(question)
            categories.add(question.category_id)
    ordered = (ordered + extras)[:count]
    challenge = DailyChallenge(challenge_date=challenge_date)
    db.session.add(challenge)
    for position, question in enumerate(ordered, 1):
        db.session.add(DailyChallengeQuestion(challenge=challenge, question=question, position=position))
    try:
        db.session.commit()
        return challenge
    except IntegrityError:
        # Another worker may have materialized this date at the same time.
        db.session.rollback()
        challenge = db.session.get(DailyChallenge, challenge_date)
        if challenge is None:
            raise
        return challenge

def current_count():
    return current_app.config["GAME_QUESTION_COUNT"]

def utc_today():
    return datetime.now(timezone.utc).date()

def utc_midnight_string(day):
    return datetime.combine(day, time.min, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

def today_payload():
    today = utc_today()
    challenge = get_or_create_daily_challenge(today)
    epoch = _parse_date(current_app.config["DAILY_EPOCH_DATE"])
    return {
        "date": today.isoformat(),
        "dayNumber": (today - epoch).days + 1,
        "serverTime": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "resetAt": utc_midnight_string(today + timedelta(days=1)),
        "questionCount": len(challenge.questions),
        "rules": {"roundCount": 7, "previewSeconds": 3, "answerSeconds": 25, "maxScore": 700},
        "questions": [public_question(row.question, row.position) for row in challenge.questions],
    }

def public_question(question, position):
    return {"promptId": f"p{position}", "prompt": question.prompt, "scope": question.scope,
            "difficulty": question.difficulty,
            "category": {"name": question.category.name, "slug": question.category.slug}}

def challenge_payload(challenge):
    return {"date": challenge.challenge_date.isoformat(),
            "questionCount": len(challenge.questions),
            "questions": [public_question(row.question, row.position) for row in challenge.questions]}

def game_payload(game):
    answered = {s.question_id: s for s in game.submissions}
    return {"date": game.challenge_date.isoformat(), "playerId": game.player_id,
        "runId": game.run_id, "score": game.score,
        "acceptedCount": len(game.submissions), "status": game.status,
        "questions": [{**public_question(gq.question, gq.position),
            "accepted": gq.question_id in answered,
            "score": answered[gq.question_id].points_awarded if gq.question_id in answered else None}
            for gq in game.questions]}

def _existing_daily_run(player_id, challenge_date, run_id):
    existing = Game.query.filter_by(player_id=player_id, challenge_date=challenge_date).first()
    if existing and existing.run_id != run_id:
        raise GameError("This player already has a run for this daily challenge.", 409, "daily_run_exists")
    return existing


def create_game(date_value, player_id, run_id):
    challenge_date = _parse_date(date_value)
    today = utc_today()
    if challenge_date != today:
        raise GameError(f"Only today's daily challenge can be started ({today.isoformat()}).", 409, "not_current_daily_challenge")
    player_id = _uuid(player_id, "playerId")
    run_id = _uuid(run_id, "runId")
    existing = _existing_daily_run(player_id, challenge_date, run_id)
    if existing:
        return existing

    challenge = get_or_create_daily_challenge(challenge_date)
    questions = list(challenge.questions)
    game = Game(player_id=player_id, run_id=run_id, challenge_date=challenge_date)
    db.session.add(game)
    for row in questions:
        db.session.add(GameQuestion(game=game, question_id=row.question_id, position=row.position))
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        existing = _existing_daily_run(player_id, challenge_date, run_id)
        if existing is None:
            raise
        return existing
    return game

def get_game(run_id):
    run_id = _uuid(run_id, "runId")
    game = Game.query.filter_by(run_id=run_id).first()
    if game is None:
        raise GameError("Daily run not found.", 404, "run_not_found")
    return game

def _tier_name(rarity_tier):
    names = current_app_config().get("RARITY_TIER_NAMES", {})
    return names.get(str(rarity_tier), f"tier_{rarity_tier}")

def current_app_config():
    from flask import current_app
    return current_app.config

def _correction_suggestion(question_id, normalized, allow_fuzzy, case_sensitive):
    # Conservative typo suggestions only. Ambiguous or weak matches stay retryable.
    if not allow_fuzzy or len(normalized) < 4:
        return None
    answers = AcceptedAnswer.query.filter_by(question_id=question_id, is_active=True).all()
    candidates = [(answer, answer.canonical) for answer in answers]
    aliases = AnswerAlias.query.join(AcceptedAnswer).filter(AcceptedAnswer.question_id == question_id, AcceptedAnswer.is_active.is_(True)).all()
    candidates.extend((alias.answer, alias.alias) for alias in aliases)
    ranked = sorted(
        ((SequenceMatcher(None, normalized, normalize_answer(label, case_sensitive)).ratio(), answer)
         for answer, label in candidates),
        key=lambda item: item[0], reverse=True)
    unique_ranked = []
    for similarity, answer in ranked:
        if all(answer.id != previous.id for _, previous in unique_ranked):
            unique_ranked.append((similarity, answer))
    if not unique_ranked or unique_ranked[0][0] < 0.88:
        return None
    if len(unique_ranked) > 1 and unique_ranked[0][0] - unique_ranked[1][0] < 0.10:
        return None
    return unique_ranked[0][1]

def submit_answer(data):
    required = ("date", "promptId", "answer", "playerId", "runId")
    if not isinstance(data, dict) or any(k not in data for k in required):
        raise GameError("date, promptId, answer, playerId, and runId are required.")
    challenge_date = _parse_date(data["date"])
    player_id = _uuid(data["playerId"], "playerId")
    run_id = _uuid(data["runId"], "runId")
    if not isinstance(data["promptId"], str) or not data["promptId"].startswith("p") or not data["promptId"][1:].isdigit():
        raise GameError("promptId must look like p1, p2, etc.", 400, "invalid_prompt_id")
    position = int(data["promptId"][1:])
    raw = data["answer"]
    if not isinstance(raw, str) or len(raw) > 256:
        raise GameError("answer must be a string of at most 256 characters.")
    preview = data.get("previewCorrection", False)
    if not isinstance(preview, bool):
        raise GameError("previewCorrection must be a boolean.")
    game = Game.query.filter_by(run_id=run_id).with_for_update().first()
    if game is None:
        raise GameError("Daily run not found.", 404, "run_not_found")
    if game.player_id != player_id or game.challenge_date != challenge_date:
        raise GameError("The player or date does not match this run.", 403, "run_mismatch")
    if game.status == "completed":
        raise GameError("This daily run is already complete.", 409, "run_completed")
    if game.challenge_date != utc_today():
        raise GameError("This daily challenge has closed at 00:00 UTC.", 409, "daily_closed")
    game_question = next((row for row in game.questions if row.position == position), None)
    if game_question is None:
        raise GameError("That prompt is not part of this daily challenge.", 404, "prompt_not_found")
    existing = GameSubmission.query.filter_by(game_id=game.id, question_id=game_question.question_id).first()
    if existing:
        receipt_payload = verify_receipt(existing.receipt_token) or {}
        return {
            "accepted": True,
            "answer": existing.accepted_answer.canonical,
            "tier": _tier_name(existing.accepted_answer.rarity_tier),
            "score": existing.points_awarded,
            "totalScore": receipt_payload.get("totalScore", game.score),
            "quip": current_app.config["QUIPS"].get(str(existing.accepted_answer.rarity_tier), "Nice catch."),
            "receipt": existing.receipt_token,
        }
    normalized = normalize_answer(raw, game_question.question.case_sensitive)
    if not normalized:
        return {"accepted": False}
    active = AcceptedAnswer.query.filter_by(question_id=game_question.question_id, is_active=True)
    match = active.filter_by(normalized=normalized).first()
    if match is None:
        match = active.join(AnswerAlias).filter(AnswerAlias.normalized == normalized).first()
    if match is None:
        if not preview:
            suggestion = _correction_suggestion(
                game_question.question_id, normalized,
                game_question.question.allow_fuzzy, game_question.question.case_sensitive,
            )
            if suggestion is not None:
                return {"accepted": False, "correction": suggestion.canonical}
        # Wrong and empty guesses are deliberately not persisted or consuming.
        return {"accepted": False}
    if match.points != current_app.config["RARITY_TIER_POINTS"].get(match.rarity_tier):
        raise GameError("The answer tier has invalid scoring data.", 503, "invalid_scoring_data")
    game.score += match.points
    tier = _tier_name(match.rarity_tier)
    issued_at = int(datetime.now(timezone.utc).timestamp() * 1000)
    receipt = issue_receipt({"v": 2, "scope": "daily", "game": game.id,
        "date": challenge_date.isoformat(), "round": position,
        "promptId": data["promptId"], "answer": match.canonical, "tier": tier,
        "playerId": player_id, "runId": run_id, "score": match.points,
        "totalScore": game.score, "issuedAt": issued_at})
    submission = GameSubmission(game=game, question=game_question.question,
        submitted_answer=raw.strip(), normalized_answer=normalized,
        points_awarded=match.points, accepted_answer=match, receipt_token=receipt)
    db.session.add(submission)
    db.session.commit()
    return {"accepted": True, "answer": match.canonical, "tier": tier,
            "score": match.points, "totalScore": game.score,
            "quip": current_app.config["QUIPS"].get(str(match.rarity_tier), "Nice catch."),
            "receipt": receipt}

def complete_game(data):
    required = ("date", "playerId", "runId", "receipts")
    if not isinstance(data, dict) or any(key not in data for key in required):
        raise GameError("date, playerId, runId, and receipts are required.")
    challenge_date = _parse_date(data["date"])
    player_id = _uuid(data["playerId"], "playerId")
    run_id = _uuid(data["runId"], "runId")
    if data.get("record") is not True:
        raise GameError("record must be true to complete a daily run.")
    receipts = data["receipts"]
    if not isinstance(receipts, list) or len(receipts) != 7:
        raise GameError("receipts must contain seven p1-to-p7 slots; use null for unanswered prompts.")
    game = Game.query.filter_by(run_id=run_id).with_for_update().first()
    if game is None:
        raise GameError("Daily run not found.", 404, "run_not_found")
    if game.player_id != player_id or game.challenge_date != challenge_date:
        raise GameError("The player or date does not match this run.", 403, "run_mismatch")
    if game.completion_summary is not None:
        return game.completion_summary
    if len(game.questions) != 7:
        raise GameError("This run does not contain seven prompts.", 503, "invalid_daily_set")
    persisted = {submission.question_id: submission for submission in game.submissions}
    for position, (game_question, token) in enumerate(zip(game.questions, receipts), start=1):
        submission = persisted.get(game_question.question_id)
        if submission is None:
            if token not in (None, ""):
                raise GameError(f"No accepted answer exists for p{position}.", 400, "receipt_mismatch")
            continue
        if not isinstance(token, str) or not hmac_compare(token, submission.receipt_token):
            raise GameError(f"Receipt does not match accepted answer p{position}.", 400, "receipt_mismatch")
        claim = verify_receipt(token)
        if not claim or claim.get("runId") != run_id or claim.get("playerId") != player_id or claim.get("date") != challenge_date.isoformat() or claim.get("round") != position:
            raise GameError(f"Receipt claims are invalid for p{position}.", 400, "receipt_mismatch")
    game.status = "completed"
    game.completed_at = datetime.now(timezone.utc)
    db.session.flush()
    scores = [row[0] for row in db.session.query(Game.score).filter_by(challenge_date=challenge_date, status="completed").all()]
    sample = len(scores)
    better_than = round(100 * sum(1 for score in scores if score <= game.score) / sample) if sample else 0
    bounds = [(0, 99), (100, 199), (200, 299), (300, 399), (400, 499), (500, 599), (600, 700)]
    dist = [{"minScore": low, "maxScore": high, "count": sum(1 for score in scores if low <= score <= high)} for low, high in bounds]
    summary = {"sample": sample, "betterThan": better_than, "dist": dist}
    game.completion_summary = summary
    db.session.commit()
    return summary

def hmac_compare(left, right):
    import hmac
    return hmac.compare_digest(left, right)
