# ROOT ACCESS

Local starter scaffold: Flask + React/TypeScript + PostgreSQL.

## Prerequisites
Install Python 3.12, Node.js LTS, Git, Docker Desktop (WSL 2 backend), and VS Code.

## Start PostgreSQL (project root)
```powershell
docker compose -f database/docker-compose.yml up -d
```

## Start backend
```powershell
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
flask --app run.py db upgrade
flask --app run.py seed
flask --app run.py run --debug
```
If activation is blocked: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`

API: http://127.0.0.1:5000/api/health and http://127.0.0.1:5000/api/questions

## Start frontend (new terminal)
```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```
Open http://localhost:5173

The starter questions are development fixtures. Review facts, aliases, provenance, licensing and rarity before public release. Never expose accepted answers through a public question-list endpoint in a live competitive game; this scaffold only lists prompts for the first connectivity milestone.
