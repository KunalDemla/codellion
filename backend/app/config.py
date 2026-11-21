import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

class Config:
    APP_ENV = os.getenv("APP_ENV", "development").lower()
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://root_access:local_only_change_me@localhost:5432/root_access",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    JSON_SORT_KEYS = False
    GAME_QUESTION_COUNT = 7
    RECEIPT_MAX_AGE_MS = int(os.getenv("RECEIPT_MAX_AGE_MS", str(30 * 24 * 60 * 60 * 1000)))
    # Daily boundaries are UTC midnight; client timers remain a presentation concern.
    DAILY_EPOCH_DATE = os.getenv("DAILY_EPOCH_DATE", "2026-01-01")
    # Keep these labels stable once content is published for a date.
    RARITY_TIER_NAMES = {
        "1": "Public", "2": "Known Trick", "3": "User Space",
        "4": "Privileged", "5": "Kernel", "6": "Root Key",
    }
    RARITY_TIER_POINTS = {1: 10, 2: 15, 3: 30, 4: 60, 5: 85, 6: 100}
    MAX_DAILY_SCORE = 700
    QUIPS = {
        "1": "A signal is born.",
        "2": "The stack is learning your name.",
        "3": "Clean execution.",
        "4": "You know your way around the system.",
        "5": "That answer left almost no trace.",
        "6": "The deep has a new legend.",
    }
