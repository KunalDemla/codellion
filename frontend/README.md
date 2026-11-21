# ROOT ACCESS frontend

React and Vite interface for Codellion’s daily programming quiz.

## Run locally

1. Start the Flask service using the instructions in the [backend README](../backend/README.md).
2. From this folder, run:

   ```sh
   npm ci
   cp .env.example .env.local
   npm run dev
   ```

Vite prints the URL to open. Its default proxy target is the local Flask
origin specified in `.env.example`.

## Frontend configuration

- `VITE_API_BASE_URL` is the API base including its prefix. The default is
  `/api`. It can be a relative path or an absolute API URL.
- `API_PROXY_TARGET` is the backend origin for Vite development and preview.
  Vite preserves the relative API prefix. For a direct cross-origin API, set
  the absolute base URL and allow the frontend origin in the backend’s
  `FRONTEND_ORIGIN` configuration.
- `VITE_API_REQUEST_TIMEOUT_MS` optionally changes the timeout for each HTTP
  request. The default is 8000 ms.
- `VITE_ANSWER_REVIEW_PATH` optionally enables the answer catalog. For an API
  that serves a post-completion answer catalog, use a relative template such as
  `/runs/{runId}/results/rounds/{roundNumber}/answers`. The endpoint accepts
  `q`, `tier`, and `cursor` and returns `items`, `tierCounts`, `total`,
  `matched`, and `nextCursor`. Each item has `id`, `label`, `tier`,
  `points`, optional `note`, and `isYourAnswer`. With the current Flask API,
  leave it blank to show the player’s own answer history.

The UI uses `GET /today` for prompts, rule settings, and the server clock,
`POST /games` to start, `POST /submit` for checks and corrections, and
`POST /today/complete` for receipt-backed scoring and standings. Round clocks
and unsent drafts belong to the browser under the current backend contract.
The browser also stores the anonymous player ID and local logbook. The API
supplies the questions and scores.

Run `npm test` and `npm run build` before submitting changes. In production
serve `dist/` and route `/api` to Flask, or set the absolute
`VITE_API_BASE_URL` at build time. Only public client settings belong in
`VITE_*` variables.
