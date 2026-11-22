import json
from collections import Counter
from datetime import timedelta
from uuid import uuid4

from app import seed
from app.extensions import db
from app.models import AcceptedAnswer, AnswerAlias, Question
from app.services.answer_validator import normalize_answer
from app.services import game_service


def load_bank():
    return json.loads((seed.SEED_DIR / seed.BANK_FILES["curated"]).read_text(encoding="utf-8"))


def test_curated_bank_covers_familiar_answers_and_keeps_the_tiers():
    bank = load_bank()
    seed.validate_seed(bank, curated=True)
    assert len(bank) == 100
    by_slug = {item["slug"].removeprefix("curated-basics-"): item for item in bank}
    for item in bank:
        tiers = Counter(answer["rarity_tier"] for answer in item["answers"])
        assert tiers[6] == 1
        assert all(tiers[level] > 1 for level in range(1, 6))
        assert item["prompt"].startswith("Name ")
        assert "java.net" not in item["prompt"]
        assert all(not text.strip().isdigit()
                   for answer in item["answers"] for text in [answer["canonical"], *answer["aliases"]])

    assert by_slug["programming-languages"]["prompt"] == "Name a programming language."
    for slug, familiar in {
        "programming-languages": {"Python", "Java", "JavaScript", "C"},
        "http-status-names": {"OK", "Not Found", "Internal Server Error", "I'm a teapot"},
        "git-commands": {"clone", "pull", "commit", "status"},
        "database-engines": {"PostgreSQL", "MySQL", "SQLite", "MongoDB"},
        "sorting-algorithms": {"merge sort", "quicksort", "bubble sort"},
        "html-elements": {"div", "a", "img"},
        "web-browsers": {"Chrome", "Firefox", "Safari", "Brave"},
        "dns-records": {"A", "AAAA", "CNAME", "MX"},
        "ci-tools": {"GitHub Actions", "Jenkins", "CircleCI"},
    }.items():
        public = {a["canonical"] for a in by_slug[slug]["answers"] if a["rarity_tier"] == 1}
        assert familiar.issubset(public)
    aggregates = by_slug["sql-aggregates"]["answers"]
    assert len(aggregates) == 12
    assert {"avg", "count", "max", "min", "sum"} <= {
        a["canonical"] for a in aggregates if a["rarity_tier"] <= 2
    }
    statuses = {answer["canonical"] for answer in by_slug["http-status-names"]["answers"]}
    assert len(statuses) == 63
    assert "IM Used" in statuses


def test_reseed_keeps_todays_runs_and_refreshes_future_lineups(client, tmp_path, monkeypatch):
    previous = Question.query.filter_by(status="approved").order_by(Question.id).first()
    previous.slug = "curated-basics-binary-shift"
    db.session.commit()
    before = client.get("/api/today").get_json()
    tomorrow = game_service.utc_today() + timedelta(days=1)
    tomorrow_path = "/api/daily-challenge?date=" + tomorrow.isoformat()
    original_preview = client.get(tomorrow_path).get_json()["questions"]

    selected = {
        "python-keywords", "css-colors", "sql-aggregates", "dns-records",
        "programming-languages", "database-engines", "http-status-names",
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
    statuses = next(item for item in next_daily["questions"] if "HTTP response status" in item["prompt"])
    keywords = next(item for item in next_daily["questions"] if "Python keyword" in item["prompt"])
    player_id, run_id = str(uuid4()), str(uuid4())
    identifiers = {"playerId": player_id, "runId": run_id, "date": next_daily["date"]}
    assert client.post("/api/games", json=identifiers).status_code == 201
    for prompt, wrong, correct in [(statuses, "404", "Not Found"), (keywords, "true", "True")]:
        guess = {**identifiers, "promptId": prompt["promptId"], "answer": wrong}
        assert not client.post("/api/submit", json=guess).get_json()["accepted"]
        result = client.post("/api/submit", json={**guess, "answer": correct}).get_json()
        assert result["accepted"]
        assert result["answer"] == correct


def test_curated_aliases_reseed_and_score_in_an_existing_run(client, tmp_path, monkeypatch):
    examples = {
        "software-licenses": ("bsl", "BSL-1.0", "BUSL"),
        "tree-structures": ("bst", "binary search tree", "binary search"),
        "data-structures": ("bt", "binary tree", "b"),
        "python-exceptions": ("typeerror", "TypeError", "typ"),
        "ci-tools": ("gha", "GitHub Actions", "GitHub"),
        "data-formats": ("comma separated values", "CSV", "comma"),
        "character-encodings": ("latin1", "ISO-8859-1", "8859"),
    }
    sample = [item for item in load_bank() if item["slug"].removeprefix("curated-basics-") in examples]
    curated_file = tmp_path / seed.BANK_FILES["curated"]
    (tmp_path / seed.BANK_FILES["starter"]).write_bytes((seed.SEED_DIR / seed.BANK_FILES["starter"]).read_bytes())
    curated_file.write_text(json.dumps(sample), encoding="utf-8")
    monkeypatch.setattr(seed, "SEED_DIR", tmp_path)
    seed.seed_questions()

    today = client.get("/api/today").get_json()
    prompt_ids = {question["prompt"]: question["promptId"] for question in today["questions"]}
    run = {"date": today["date"], "playerId": str(uuid4()), "runId": str(uuid4())}
    assert client.post("/api/games", json=run).status_code == 201

    for item in sample:
        alias, canonical, _ = examples[item["slug"].removeprefix("curated-basics-")]
        question = Question.query.filter_by(slug=item["slug"]).one()
        answer = AcceptedAnswer.query.filter_by(question_id=question.id, canonical=canonical).one()
        AnswerAlias.query.filter_by(
            answer_id=answer.id, normalized=normalize_answer(alias, question.case_sensitive),
        ).delete()
    db.session.commit()

    first = sample[0]
    alias = examples[first["slug"].removeprefix("curated-basics-")][0]
    guess = {**run, "promptId": prompt_ids[first["prompt"]], "answer": alias}
    assert client.post("/api/submit", json=guess).get_json() == {"accepted": False}

    seed.seed_questions()
    seed.seed_questions()
    assert client.get("/api/today").get_json()["questions"] == today["questions"]
    for item in sample:
        alias, canonical, invalid = examples[item["slug"].removeprefix("curated-basics-")]
        expected = next(answer for answer in item["answers"] if answer["canonical"] == canonical)
        guess = {**run, "promptId": prompt_ids[item["prompt"]], "answer": invalid}
        assert client.post("/api/submit", json=guess).get_json() == {"accepted": False}
        result = client.post("/api/submit", json={**guess, "answer": alias}).get_json()
        assert (result["accepted"], result["answer"], result["score"]) == (True, canonical, expected["points"])
