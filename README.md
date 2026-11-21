# ROOT ACCESS

ROOT ACCESS is a daily, hacker-themed knowledge game. The backend is Flask + PostgreSQL; the frontend is React + TypeScript.

## Backend

See [`backend/README.md`](backend/README.md) for Windows setup, PostgreSQL configuration, migrations, API contracts, daily challenge behavior, alias confirmation, signed receipts, and tests.

## Frontend

The React/Vite frontend lives in `frontend/`. It should fetch the daily challenge, create a run with a player UUID and run UUID, own the timer, and submit answers using the backend contract documented in `backend/README.md`.

## Database

`database/docker-compose.yml` is an optional local PostgreSQL setup. Docker Desktop is not required if PostgreSQL is installed directly on Windows.
