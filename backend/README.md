# ROOT ACCESS — Daily Challenge Backend

Flask + SQLAlchemy + PostgreSQL backend. The daily challenge changes at **00:00 UTC**. Each UTC date has the same seven prompts in the same order for every player. The React client owns the preview and answer countdowns; the backend does not measure per-question time.

## Rules

- Seven prompts per daily challenge; the maximum score is 700.
- Tiers and points are `Public` 10, `Known Trick` 15, `User Space` 30, `Privileged` 60, `Kernel` 85, and `Root Key` 100.
- Exact canonical answers and aliases are accepted immediately and earn the same score. A confident typo match can return `accepted: false` with a suggested `correction` when fuzzy matching is enabled for that question. Submit the suggested answer to confirm it. Only accepted answers are recorded and consume that prompt.
- Incorrect, empty, ambiguous, or unconfirmed guesses are not recorded. A player may retry until the client timer ends. The backend closes submissions when the UTC daily challenge rolls over.
- One run per `playerId` per UTC date. `playerId` and `runId` are UUIDs; account authentication is not implemented yet.
- Scores are computed by the server. Accepted answers return a signed HMAC-SHA256 receipt. Receipts are persisted so repeating an accepted submission returns the original result.
- Public daily/run responses do not expose canonical answers, aliases, or rarity data.
- Question sets are materialized and persisted when the date is first requested. Do not run the seed command or edit answer data during a live daily; content is not snapshotted separately from the question bank.

## Local setup

Python 3.12 and PostgreSQL 15+ are recommended. Use a native PostgreSQL installation or the optional Docker Compose setup in `../database`.

### Windows

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

### macOS and Linux

```sh
cd backend
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

### Database and API

Create a PostgreSQL database and a login role that owns it. Set `DATABASE_URL`
in `.env` to that role’s connection URL and set a strong random `SECRET_KEY`.
Set `FRONTEND_ORIGIN` to the frontend URL when running directly across origins.
`APP_ENV=production` requires a secret of at least 32 characters.
`DAILY_EPOCH_DATE` controls the day number and the reset remains midnight UTC.

Apply the checked-in migrations, load the curated questions, and start Flask
from `backend/` with the virtual environment active.

```sh
flask --app run.py db upgrade
flask --app run.py seed
flask --app run.py run
```

Run `flask --app run.py db current` to inspect the applied revision. For model
changes, generate and inspect a new migration with `flask --app run.py db
migrate -m "Describe the schema change"` before applying it. The API health
endpoint is `GET /api/health`.

## API

### `GET /api/today`

Returns today's UTC date, stable day number, next reset instant, timing display settings, and seven public prompts. Example shape:

```json
{
  "date": "2026-11-22",
  "dayNumber": 326,
  "serverTime": "2026-11-22T12:00:00Z",
  "resetAt": "2026-11-23T00:00:00Z",
  "questionCount": 7,
  "rules": {"roundCount": 7, "previewSeconds": 3, "answerSeconds": 25, "maxScore": 700},
  "questions": [{"promptId": "p1", "prompt": "...", "scope": "...", "difficulty": 1, "category": {"name": "...", "slug": "..."}}]
}
```

### `POST /api/games`

Create or resume today's run:

```json
{"date":"2026-11-22","playerId":"54170d9f-fb20-499a-ac66-faa75de4d844","runId":"f03a8a3d-98ed-4eec-b307-dad37b9e93ee"}
```

The same player/date/run ID resumes the existing run. A different run ID for the same player/date is rejected.

### `POST /api/submit`

Submit or preview an answer:

```json
{"date":"2026-11-22","promptId":"p3","answer":"SHA256","previewCorrection":false,"playerId":"54170d9f-fb20-499a-ac66-faa75de4d844","runId":"f03a8a3d-98ed-4eec-b307-dad37b9e93ee"}
```

An incorrect answer returns `{"accepted":false}`. When fuzzy matching is enabled, a confident typo can return `{"accepted":false,"correction":"SHA-256"}`. An exact match such as `SHA256` returns the canonical answer and its score, for example `{"accepted":true,"answer":"SHA-256","tier":"Public","score":10,"totalScore":10,"quip":"A signal is born.","receipt":"<signed-token>"}`.

The compatible `POST /api/games/{runId}/answers` route is also available.

### `POST /api/today/complete`

Completes and records the run after the client finishes its seven rounds:

```json
{"date":"2026-11-22","playerId":"54170d9f-fb20-499a-ac66-faa75de4d844","score":10,"record":true,"runId":"f03a8a3d-98ed-4eec-b307-dad37b9e93ee","receipts":["<p1-receipt>",null,null,null,null,null,null]}
```

`receipts` has seven slots in p1-to-p7 order. A slot is the accepted answer's receipt or `null` when that prompt received no correct answer. The server verifies receipts, ignores the submitted `score`, and calculates the stored score from accepted submissions. Response: `{ "sample": 1, "betterThan": 100, "dist": [{"minScore":0,"maxScore":99,"count":1}, ...] }`. The histogram spans 0–700 in 100-point bands. Completion is idempotent and returns the saved summary on retries.

### Other routes

- `GET /api/games/{runId}` — run progress and accepted prompt scores, without answer keys.
- `GET /api/daily-leaderboard?date=YYYY-MM-DD` — up to 100 completed runs for that UTC date.
- `POST /api/receipts/verify` — verifies the signature and receipt age.
- `GET /api/daily-challenge?date=YYYY-MM-DD` — public prompt list for a specific date.
- `GET /api/categories` — category metadata.

## Seed content

The default seed loads the 100-prompt curated bank from
`seed/curated_questions.json`. Each prompt has a complete answer set within
its displayed scope. Answer counts vary with the topic. The first five tiers
carry multiple answers and Root Key has one. The starter prompts are available via `flask --app run.py seed
--bank starter` for development.

See the [seed data plan](seed/SEED_DATA_PLAN.md) for source provenance,
rebuilding the bank, and safe publication around the UTC reset.
