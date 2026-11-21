import itertools
import json
from collections import Counter
from datetime import timedelta
from uuid import uuid4

from app import seed
from app.extensions import db
from app.models import AcceptedAnswer, Question
from app.services import game_service


def load_bank():
    return json.loads((seed.SEED_DIR / seed.BANK_FILES["curated"]).read_text(encoding="utf-8"))


def answer_names(question):
    return {answer["canonical"] for answer in question["answers"]}


def test_curated_bank_covers_familiar_answers_and_keeps_the_tiers():
    bank = load_bank()
    seed.validate_seed(bank, curated=True)
    assert len(bank) == 100
    by_slug = {item["slug"].removeprefix("curated-basics-"): item for item in bank}
    for item in bank:
        tiers = Counter(answer["rarity_tier"] for answer in item["answers"])
        assert tiers[6] == 1
        assert all(tiers[level] > 1 for level in range(1, 6))
        assert "java.net" not in item["prompt"]

    assert by_slug["programming-languages"]["prompt"] == "Name a programming language."
    for slug, familiar in {
        "programming-languages": {"Python", "Java", "JavaScript", "C"},
        "http-status": {"200", "404", "500", "418"},
        "git-commands": {"clone", "pull", "commit", "status"},
        "database-engines": {"PostgreSQL", "MySQL", "SQLite", "MongoDB"},
        "sorting-algorithms": {"merge sort", "quicksort", "bubble sort"},
        "html-elements": {"div", "a", "img"},
    }.items():
        public = {a["canonical"] for a in by_slug[slug]["answers"] if a["rarity_tier"] == 1}
        assert familiar.issubset(public)
    aggregates = by_slug["sql-aggregates"]["answers"]
    assert len(aggregates) == 12
    assert {"avg", "count", "max", "min", "sum"} <= {
        a["canonical"] for a in aggregates if a["rarity_tier"] <= 2
    }
    assert answer_names(by_slug["hex-byte"]) == {f"{n:02X}" for n in range(256)}
    assert answer_names(by_slug["reg-ex-pair"]) == {
        a + b for a, b in itertools.product("abcdefghijklmnopqrstuvwxyz", "0123456789")
    }
    assert answer_names(by_slug["json-one-character"]) == {json.dumps(chr(n)) for n in range(32, 127)}


def test_reseed_keeps_todays_runs_and_refreshes_future_lineups(client, tmp_path, monkeypatch):
    previous = Question.query.filter_by(status="approved").order_by(Question.id).first()
    previous.slug = "curated-old-question"
    db.session.commit()
    before = client.get("/api/today").get_json()
    tomorrow = game_service.utc_today() + timedelta(days=1)
    tomorrow_path = "/api/daily-challenge?date=" + tomorrow.isoformat()
    original_preview = client.get(tomorrow_path).get_json()["questions"]

    selected = {
        "json-one-character", "css-colors", "sql-aggregates", "python-modules",
        "programming-languages", "database-engines", "http-status",
    }
    sample = [item for item in load_bank() if item["slug"].removeprefix("curated-basics-") in selected]
    for name in seed.BANK_FILES.values():
        source = seed.SEED_DIR / name
        (tmp_path / name).write_text(json.dumps(sample) if name == seed.BANK_FILES["curated"]
                                    else source.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(seed, "SEED_DIR", tmp_path)
    seed.seed_questions("curated")
    assert client.get("/api/today").get_json()["questions"] == before["questions"]
    assert previous.status == "retired"
    assert Question.query.filter_by(status="approved").count() == 7
    preview = client.get(tomorrow_path).get_json()["questions"]
    assert preview != original_preview
    assert all(prompt["scope"] for prompt in preview)
    count = AcceptedAnswer.query.filter_by(is_active=True).count()
    seed.seed_questions("curated")
    assert AcceptedAnswer.query.filter_by(is_active=True).count() == count
    assert client.get(tomorrow_path).get_json()["questions"] == preview

    monkeypatch.setattr(game_service, "utc_today", lambda: tomorrow)
    next_daily = client.get("/api/today").get_json()
    assert len(next_daily["questions"]) == 7
    prompt = next(item for item in next_daily["questions"] if "printable ASCII" in item["prompt"])
    for raw in ('"a"', '"A"'):
        player_id, run_id = str(uuid4()), str(uuid4())
        identifiers = {"playerId": player_id, "runId": run_id, "date": next_daily["date"]}
        assert client.post("/api/games", json=identifiers).status_code == 201
        reply = client.post("/api/submit", json={**identifiers, "promptId": prompt["promptId"], "answer": raw})
        assert reply.get_json()["accepted"]
        assert reply.get_json()["answer"] == raw
