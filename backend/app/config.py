import os
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "local-only")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql+psycopg://root_access:local_only_change_me@localhost:5432/root_access")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
