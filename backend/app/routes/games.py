from flask import Blueprint, jsonify, request, current_app
from app.services.answer_review import review_answers
from app.services.game_service import (GameError, create_game, get_game,
    game_payload, submit_answer, complete_game, today_payload,
    get_or_create_daily_challenge, challenge_payload, _parse_date)
from app.services.receipt import verify_receipt
from app.models import Game

bp = Blueprint("games", __name__)

def error_response(error):
    return jsonify({"error": {"code": error.code, "message": error.message}}), error.status_code

@bp.get("/daily-challenge")
def daily_challenge():
    try:
        date_value = request.args.get("date")
        if not date_value:
            return jsonify({"error": {"code": "missing_date", "message": "date query parameter is required (YYYY-MM-DD)."}}), 400
        challenge = get_or_create_daily_challenge(_parse_date(date_value))
        return jsonify(challenge_payload(challenge))
    except GameError as error:
        return error_response(error)

@bp.get("/today")
def today():
    try:
        return jsonify(today_payload()), 200, {"Cache-Control": "no-store"}
    except GameError as error:
        return error_response(error)

@bp.post("/games")
def start_game():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": {"code": "invalid_json", "message": "A JSON object is required."}}), 400
    try:
        game = create_game(body.get("date"), body.get("playerId"), body.get("runId"))
        return jsonify(game_payload(game)), 201
    except GameError as error:
        return error_response(error)

@bp.get("/games/<run_id>")
def game_status(run_id):
    try:
        return jsonify(game_payload(get_game(run_id)))
    except GameError as error:
        return error_response(error)

@bp.get("/games/<run_id>/results/rounds/<int:round_number>/answers")
def round_answers(run_id, round_number):
    try:
        catalog = review_answers(
            run_id, request.args.get("playerId"), round_number,
            q=request.args.get("q", ""), tier=request.args.get("tier", ""), cursor=request.args.get("cursor", ""),
        )
        return jsonify(catalog), 200, {"Cache-Control": "private, no-store"}
    except GameError as error:
        return error_response(error)

@bp.post("/games/<run_id>/answers")
def answer_question(run_id):
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": {"code": "invalid_json", "message": "A JSON object is required."}}), 400
    if body.get("runId") != run_id:
        return jsonify({"error": {"code": "run_mismatch", "message": "URL runId and body runId must match."}}), 400
    try:
        return jsonify(submit_answer(body)), 200
    except GameError as error:
        return error_response(error)

@bp.post("/submit")
def submit():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": {"code": "invalid_json", "message": "A JSON object is required."}}), 400
    try:
        return jsonify(submit_answer(body)), 200
    except GameError as error:
        return error_response(error)

@bp.post("/today/complete")
def complete_today():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"error": {"code": "invalid_json", "message": "A JSON object is required."}}), 400
    try:
        return jsonify(complete_game(body)), 200
    except GameError as error:
        return error_response(error)

@bp.post("/receipts/verify")
def receipt_verify():
    body = request.get_json(silent=True)
    token = body.get("receipt") if isinstance(body, dict) else None
    if not isinstance(token, str):
        return jsonify({"valid": False}), 400
    payload = verify_receipt(token)
    return jsonify({"valid": payload is not None, "receipt": payload}), (200 if payload else 400)

@bp.get("/daily-leaderboard")
def daily_leaderboard():
    date_value = request.args.get("date")
    try:
        challenge_date = _parse_date(date_value)
    except GameError as error:
        return error_response(error)
    # A player's single daily run is ranked by its accepted-answer total.
    rows = (Game.query.filter_by(challenge_date=challenge_date, status="completed")
        .order_by(Game.score.desc(), Game.created_at.asc()).limit(100).all())
    return jsonify({"date": challenge_date.isoformat(), "entries": [
        {"rank": index, "playerId": row.player_id, "score": row.score,
         "acceptedCount": len(row.submissions)} for index, row in enumerate(rows, 1)]})
