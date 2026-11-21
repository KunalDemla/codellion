import uuid
from datetime import datetime, timezone
from app.models import Game

PLAYER_A = str(uuid.uuid4())
PLAYER_B = str(uuid.uuid4())

def game_date():
    return datetime.now(timezone.utc).date().isoformat()

def start(client, player=PLAYER_A, run=None, date=None):
    date = date or game_date()
    run = run or str(uuid.uuid4())
    response = client.post("/api/games", json={"date": date, "playerId": player, "runId": run})
    assert response.status_code == 201, response.get_json()
    return response.get_json()

def test_daily_questions_are_identical_for_all_players(client):
    a = start(client, PLAYER_A)
    b = start(client, PLAYER_B)
    assert [(q["promptId"], q["prompt"]) for q in a["questions"]] == [(q["promptId"], q["prompt"]) for q in b["questions"]]
    assert a["date"] == b["date"]
    assert len(a["questions"]) == 7

def test_today_returns_utc_daily_and_public_prompts(client):
    result = client.get("/api/today").get_json()
    assert result["date"] == game_date()
    assert result["questionCount"] == 7
    assert result["rules"]["maxScore"] == 700
    assert result["resetAt"].endswith("T00:00:00Z")
    assert [question["promptId"] for question in result["questions"]] == [f"p{i}" for i in range(1, 8)]
    assert "canonical" not in str(result).lower()

def test_wrong_answers_do_not_consume_prompt(client):
    game = start(client)
    q = next(q for q in game["questions"] if q["prompt"] == "Name a cryptographic hash function.")
    body = {"date": game["date"], "promptId": q["promptId"], "answer": "not-a-hash", "previewCorrection": False, "playerId": PLAYER_A, "runId": game["runId"]}
    assert client.post("/api/submit", json=body).get_json() == {"accepted": False}
    assert client.post("/api/submit", json=body).get_json() == {"accepted": False}
    status = client.get(f"/api/games/{game['runId']}").get_json()
    assert status["acceptedCount"] == 0
    assert status["score"] == 0

def test_alias_returns_correction_then_confirmation_accepts(client):
    game = start(client)
    q = next(q for q in game["questions"] if q["prompt"] == "Name a cryptographic hash function.")
    body = {"date": game["date"], "promptId": q["promptId"], "answer": "SHA256", "previewCorrection": False, "playerId": PLAYER_A, "runId": game["runId"]}
    preview = client.post("/api/submit", json=body)
    assert preview.status_code == 200
    assert preview.get_json() == {"accepted": False, "correction": "SHA-256"}
    assert client.get(f"/api/games/{game['runId']}").get_json()["acceptedCount"] == 0
    body["previewCorrection"] = True
    confirmed = client.post("/api/submit", json=body)
    data = confirmed.get_json()
    assert confirmed.status_code == 200
    assert data["accepted"] is True
    assert data["answer"] == "SHA-256"
    assert data["tier"] == "Public"
    assert data["score"] == 10
    assert data["quip"]
    assert data["receipt"]
    assert client.get(f"/api/games/{game['runId']}").get_json()["acceptedCount"] == 1

def test_similar_answer_suggests_correction_without_consuming_prompt(client):
    game = start(client)
    q = next(q for q in game["questions"] if q["prompt"] == "Name a cryptographic hash function.")
    body = {"date": game["date"], "promptId": q["promptId"], "answer": "SHA-25", "previewCorrection": False, "playerId": PLAYER_A, "runId": game["runId"]}
    response = client.post("/api/submit", json=body)
    assert response.get_json() == {"accepted": False, "correction": "SHA-256"}
    assert client.get(f"/api/games/{game['runId']}").get_json()["acceptedCount"] == 0

def test_correct_canonical_answer_is_accepted_immediately(client):
    game = start(client)
    q = next(q for q in game["questions"] if q["prompt"] == "Name a cryptographic hash function.")
    body = {"date": game["date"], "promptId": q["promptId"], "answer": "SHA-256", "previewCorrection": False, "playerId": PLAYER_A, "runId": game["runId"]}
    result = client.post("/api/submit", json=body).get_json()
    assert result["accepted"] is True
    assert result["score"] == 10

def test_repeating_accepted_submission_replays_original_receipt(client):
    game = start(client)
    q = next(q for q in game["questions"] if q["prompt"] == "Name a cryptographic hash function.")
    body = {"date": game["date"], "promptId": q["promptId"], "answer": "SHA-256", "previewCorrection": False, "playerId": PLAYER_A, "runId": game["runId"]}
    first = client.post("/api/submit", json=body).get_json()
    second = client.post("/api/submit", json=body)
    assert second.status_code == 200
    assert second.get_json() == first

def test_one_run_per_player_per_day(client):
    start(client)
    response = client.post("/api/games", json={"date": game_date(), "playerId": PLAYER_A, "runId": str(uuid.uuid4())})
    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "daily_run_exists"

def test_receipt_verification(client):
    game = start(client)
    q = next(q for q in game["questions"] if q["prompt"] == "Name a cryptographic hash function.")
    body = {"date": game["date"], "promptId": q["promptId"], "answer": "SHA-256", "previewCorrection": False, "playerId": PLAYER_A, "runId": game["runId"]}
    accepted = client.post("/api/submit", json=body).get_json()
    verify = client.post("/api/receipts/verify", json={"receipt": accepted["receipt"]})
    assert verify.status_code == 200
    assert verify.get_json()["valid"] is True
    assert verify.get_json()["receipt"]["playerId"] == PLAYER_A

def test_completion_verifies_receipts_and_uses_server_score(client):
    game = start(client)
    q = next(q for q in game["questions"] if q["prompt"] == "Name a cryptographic hash function.")
    body = {"date": game["date"], "promptId": q["promptId"], "answer": "SHA-256", "previewCorrection": False, "playerId": PLAYER_A, "runId": game["runId"]}
    accepted = client.post("/api/submit", json=body).get_json()
    receipts = [None] * 7
    receipts[int(q["promptId"][1:]) - 1] = accepted["receipt"]
    completion = {"date": game["date"], "playerId": PLAYER_A, "score": 700, "record": True, "runId": game["runId"], "receipts": receipts}
    result = client.post("/api/today/complete", json=completion)
    assert result.status_code == 200
    summary = result.get_json()
    assert summary["sample"] == 1
    assert summary["betterThan"] == 100
    assert sum(bucket["count"] for bucket in summary["dist"]) == 1
    leaderboard = client.get(f"/api/daily-leaderboard?date={game['date']}").get_json()
    assert leaderboard["entries"][0]["score"] == 10
    assert client.post("/api/today/complete", json=completion).get_json() == summary

def test_six_tiers_can_reach_700_points(client, app):
    expected = [
        ("Public", 10), ("Known Trick", 15), ("User Space", 30),
        ("Privileged", 60), ("Kernel", 85), ("Root Key", 100),
    ]
    with app.app_context():
        assert list(zip(app.config["RARITY_TIER_NAMES"].values(), app.config["RARITY_TIER_POINTS"].values())) == expected
    game = start(client)
    with app.app_context():
        game_row = Game.query.filter_by(run_id=game["runId"]).one()
        assigned = [(row.position, row.question, next(a for a in row.question.answers if a.rarity_tier == 6)) for row in game_row.questions]
    receipts = [None] * 7
    total = 0
    for position, question, answer in assigned:
        body = {"date": game["date"], "promptId": f"p{position}", "answer": answer.canonical,
                "previewCorrection": False, "playerId": PLAYER_A, "runId": game["runId"]}
        result = client.post("/api/submit", json=body).get_json()
        assert result["accepted"] is True
        assert result["tier"] == "Root Key"
        total += result["score"]
        receipts[position - 1] = result["receipt"]
    assert total == 700
    completion = {"date": game["date"], "playerId": PLAYER_A, "score": total,
                  "record": True, "runId": game["runId"], "receipts": receipts}
    assert client.post("/api/today/complete", json=completion).status_code == 200

def test_questions_never_expose_answer_key(client):
    game = start(client)
    serialized = str(game).lower()
    assert "canonical" not in serialized
    assert "rarity_tier" not in serialized
    assert "accepted_answers" not in serialized
