# ROOT ACCESS — Daily Challenge Backend

Flask + SQLAlchemy + PostgreSQL backend. The daily challenge changes at **00:00 UTC**. Each UTC date has the same seven prompts in the same order for every player. The React client owns the preview and answer countdowns; the backend does not measure per-question time.

## Rules

- Seven prompts per daily challenge; the maximum score is 700.
- Tiers and points are `Public` 10, `Known Trick` 15, `User Space` 30, `Privileged` 60, `Kernel` 85, and `Root Key` 100.
- A canonical correct answer is accepted immediately. An exact alias or a confident typo match returns `accepted: false` with a suggested `correction`; the client asks the player to confirm. Confirm an exact alias by resending it with `previewCorrection: true`, or submit the displayed canonical correction. Only accepted answers are recorded and consume that prompt.
- Incorrect, empty, ambiguous, or unconfirmed guesses are not recorded. A player may retry until the client timer ends. The backend closes submissions when the UTC daily challenge rolls over.
- One run per `playerId` per UTC date. `playerId` and `runId` are UUIDs; account authentication is not implemented yet.
- Scores are computed by the server. Accepted answers return a signed HMAC-SHA256 receipt. Receipts are persisted so repeating an accepted submission returns the original result.
- Public daily/run responses do not expose canonical answers, aliases, or rarity data.
- Question sets are materialized and persisted when the date is first requested. Do not run the seed command or edit answer data during a live daily; content is not snapshotted separately from the question bank.

## Windows setup

Python 3.12 and PostgreSQL 15+ are recommended. Docker Desktop is optional; native PostgreSQL works.

```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Set a strong random `SECRET_KEY` and a working PostgreSQL `DATABASE_URL` in `.env`. `APP_ENV=production` rejects the development fallback secret and secrets shorter than 32 characters. Set `DAILY_EPOCH_DATE` to the first date of the day-number sequence if you want a different epoch; it does not change the midnight UTC boundary.

For a new database, initialize and apply migrations, then load the curated seed:

```powershell
flask --app run.py db init
flask --app run.py db migrate -m "initial daily challenge backend"
flask --app run.py db upgrade
flask --app run.py seed
```

If `migrations/` already exists, skip `db init`. For an existing database, generate and inspect a migration after updating the models, then run `flask --app run.py db upgrade`. Do not use `db.create_all()` as a production schema update.

Start Flask locally with `flask --app run.py run --debug`. Health check: `GET /api/health`.

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
  "questions": [{"promptId": "p1", "prompt": "...", "difficulty": 1, "category": {"name": "...", "slug": "..."}}]
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

Incorrect answer: `{"accepted":false}`. Alias or confident typo: `{"accepted":false,"correction":"SHA-256"}`. The correction is only a suggestion; it is not recorded until confirmed. Accepted answer: `{"accepted":true,"answer":"SHA-256","tier":"Public","score":10,"totalScore":10,"quip":"A signal is born.","receipt":"<signed-token>"}`.

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

`seed/questions.json` contains an initial bank of fourteen development prompts; each daily selects seven. Every prompt has six answer tiers. The rarity values are editorial starter values, not measured player-population statistics. Review factual answers and aliases before public launch. The seed command validates tier coverage, point values, and normalized answer/alias uniqueness before applying changes.
