FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --system --no-create-home codellion

COPY backend/app ./app
COPY backend/migrations ./migrations
COPY backend/seed/*questions.json ./seed/
COPY backend/run.py .

USER codellion
CMD ["sh", "-c", "flask --app run.py db upgrade && flask --app run.py seed --bank curated && exec gunicorn --bind 0.0.0.0:8000 --workers 2 --access-logfile - --error-logfile - run:app"]
