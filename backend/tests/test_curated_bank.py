import base64
import json
from collections import Counter
from datetime import timedelta
from uuid import uuid4


from app import seed
from app.models import AcceptedAnswer, Question
from app.services import game_service


def load_bank():
    return json.loads((seed.SEED_DIR / seed.BANK_FILES["curated"]).read_text(encoding="utf-8"))


def test_curated_bank_covers_every_byte_and_preserves_all_tiers():
    bank = load_bank()
    seed.validate_seed(bank, curated=True)
    assert len(bank) == 100
    by_slug = {item["slug"]: item for item in bank}
    for item in bank:
        tiers = Counter(answer["rarity_tier"] for answer in item["answers"])
        assert tiers[6] == 1
        assert all(tiers[level] > 1 for level in range(1, 6))
    byte = by_slug["curated-base64-one-byte"]
    assert byte["case_sensitive"] and not byte["allow_fuzzy"]
    assert {answer["canonical"] for answer in byte["answers"]} == {
        base64.b64encode(bytes([number])).decode() for number in range(256)
    }
    assert len(by_slug["curated-css-color-names"]["answers"]) == 148
    assert len(by_slug["curated-balanced-brackets"]["answers"]) == 132
    assert len(by_slug["curated-sqlite-keywords"]["answers"]) == 147
    for slug, name in [("curated-html-attributes", "href"), ("curated-svg-attributes", "viewBox")]:
        assert name in {answer["canonical"] for answer in by_slug[slug]["answers"]}
    collection_methods = {answer["canonical"] for answer in by_slug["curated-java-collection-methods"]["answers"]}
    assert "List.of" in collection_methods
    assert "List.getActionListeners" not in collection_methods


def test_seed_retires_starters_for_new_dailies_without_changing_live_rounds(client, tmp_path, monkeypatch):
    before = client.get("/api/today").get_json()
    bank = load_bank()
    sample = [item for item in bank if item["slug"] in {
        "curated-base64-one-byte", "curated-css-color-names", "curated-sqlite-keywords",
        "curated-py-os", "curated-linguist-programming", "curated-iana-character-sets",
        "curated-byte-even-parity",
    }]
    for name in seed.BANK_FILES.values():
        source = seed.SEED_DIR / name
        (tmp_path / name).write_text(json.dumps(sample) if name == seed.BANK_FILES["curated"]
                                    else source.read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(seed, "SEED_DIR", tmp_path)
    seed.seed_questions("curated")
    again = client.get("/api/today").get_json()
    assert again["questions"] == before["questions"]
    assert Question.query.filter_by(status="approved").count() == 7
    count = AcceptedAnswer.query.filter_by(is_active=True).count()
    seed.seed_questions("curated")
    assert AcceptedAnswer.query.filter_by(is_active=True).count() == count

    tomorrow = game_service.utc_today() + timedelta(days=1)
    monkeypatch.setattr(game_service, "utc_today", lambda: tomorrow)
    next_daily = client.get("/api/today").get_json()
    assert len(next_daily["questions"]) == 7
    assert all(item["scope"] for item in next_daily["questions"])
    prompt = next(item for item in next_daily["questions"] if "Base64" in item["prompt"])
    for raw in ("AA==", "aA=="):
        player_id, run_id = str(uuid4()), str(uuid4())
        identifiers = {"playerId": player_id, "runId": run_id, "date": next_daily["date"]}
        assert client.post("/api/games", json=identifiers).status_code == 201
        result = client.post("/api/submit", json={**identifiers, "promptId": prompt["promptId"], "answer": raw})
        assert result.get_json()["accepted"]
        assert result.get_json()["answer"] == raw
