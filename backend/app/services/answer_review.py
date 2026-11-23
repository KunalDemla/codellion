import re

from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload

from app.models import AcceptedAnswer, AnswerAlias, GameSubmission
from .answer_validator import normalize_answer
from .game_service import GameError, _uuid, get_game

TIER_KEYS = dict(enumerate(("common", "too_clever", "familiar", "rare", "deep_cut", "featured"), 1))
PAGE_SIZE = 50


def review_answers(run_id, player_id, round_number, *, q="", tier="", cursor=""):
    player_id = _uuid(player_id, "playerId")
    game = get_game(run_id)
    if game.player_id != player_id:
        raise GameError("The player does not match this run.", 403, "run_mismatch")
    if game.status != "completed":
        raise GameError("Finish the run to reveal its answers.", 409, "run_incomplete")
    slot = next((slot for slot in game.questions if slot.position == round_number), None)
    if slot is None:
        raise GameError("That prompt is not part of this run.", 404, "prompt_not_found")
    if len(q) > 128:
        raise GameError("Search must be at most 128 characters.")
    if "\x00" in q:
        raise GameError("Invalid search text.")
    if cursor and not re.fullmatch(r"[0-9]{1,7}", cursor):
        raise GameError("Invalid answer page cursor.")
    tier_number = next((number for number, key in TIER_KEYS.items() if key == tier), None)
    if tier and tier_number is None:
        raise GameError("Unknown answer tier.")

    offset = int(cursor or 0)
    answers = AcceptedAnswer.query.filter_by(question_id=slot.question_id, is_active=True)
    tier_counts = dict.fromkeys(TIER_KEYS.values(), 0)
    for number, count in (answers.with_entities(AcceptedAnswer.rarity_tier, func.count())
                          .group_by(AcceptedAnswer.rarity_tier)):
        tier_counts[TIER_KEYS[number]] = count
    total = sum(tier_counts.values())

    matches = answers.filter_by(rarity_tier=tier_number) if tier else answers
    matched = tier_counts[tier] if tier else total
    term = normalize_answer(q)
    if term:
        canonical = AcceptedAnswer.normalized
        alias = AnswerAlias.normalized
        if slot.question.case_sensitive:
            canonical, alias = func.lower(canonical), func.lower(alias)
        matches = matches.filter(or_(
            canonical.contains(term, autoescape=True),
            AcceptedAnswer.aliases.any(alias.contains(term, autoescape=True)),
        ))
        matched = matches.count()
    page = (matches.options(selectinload(AcceptedAnswer.aliases))
            .order_by(AcceptedAnswer.rarity_tier.desc(), AcceptedAnswer.normalized, AcceptedAnswer.id)
            .offset(offset).limit(PAGE_SIZE).all())
    own_answer = GameSubmission.query.filter_by(game_id=game.id, question_id=slot.question_id).first()
    return {
        "items": [{
            "id": answer.id,
            "label": answer.canonical,
            "tier": TIER_KEYS[answer.rarity_tier],
            "points": answer.points,
            "note": answer.explanation,
            "aliases": sorted((alias.alias for alias in answer.aliases), key=str.casefold),
            "isYourAnswer": own_answer is not None and own_answer.accepted_answer_id == answer.id,
        } for answer in page],
        "total": total,
        "matched": matched,
        "tierCounts": tier_counts,
        "nextCursor": str(offset + len(page)) if page and offset + len(page) < matched else None,
    }
