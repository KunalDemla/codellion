# ROOT ACCESS

ROOT ACCESS is a daily, hacker-themed knowledge game. The backend is Flask + PostgreSQL; the frontend is React + Vite.

## Backend

See [`backend/README.md`](backend/README.md) for local setup, PostgreSQL configuration, migrations, API contracts, daily challenge behavior, alias confirmation, signed receipts, and tests.

## Frontend

The React/Vite frontend lives in `frontend/`. Configure its API connection using `frontend/.env.example`. The API contract is documented in `backend/README.md`.

## Database

`database/docker-compose.yml` is an optional local PostgreSQL setup. Docker Desktop is not required if PostgreSQL is installed directly on Windows.

## Hosting

From the repository root, create a private Compose `.env` file. Generate separate hex values for `POSTGRES_PASSWORD` and `SECRET_KEY` with `openssl rand -hex 32`. The password is also used in a database URL, so use hex to keep it URL-safe.

```dotenv
POSTGRES_PASSWORD=<generated hex value>
SECRET_KEY=<different generated hex value>
BIND_ADDRESS=127.0.0.1
HTTP_PORT=8082
FRONTEND_ORIGIN=http://localhost:8082
```

For LAN access, set `BIND_ADDRESS` to the host's LAN address and use that address and port in `FRONTEND_ORIGIN`. Start or update the stack with `docker compose up -d --build --wait`. The frontend serves the API at `/api` on the same address. The backend applies migrations and loads the curated bank at startup. PostgreSQL data persists in the `codellion_pgdata` Docker volume.
