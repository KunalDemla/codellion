import uuid
from datetime import datetime, timezone
from app.extensions import db

def utcnow():
    return datetime.now(timezone.utc)

class Game(db.Model):
    __tablename__ = "games"
    __table_args__ = (db.UniqueConstraint("player_id", "challenge_date", name="uq_player_daily_run"),)
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = db.Column(db.String(36), nullable=False, unique=True, index=True)
    player_id = db.Column(db.String(36), nullable=False, index=True)
    challenge_date = db.Column(db.Date, db.ForeignKey("daily_challenges.challenge_date"), nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default="in_progress", index=True)
    score = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    completed_at = db.Column(db.DateTime(timezone=True))
    completion_summary = db.Column(db.JSON)
    # The frontend owns the timer. The backend deliberately does not expire or complete a run.
    questions = db.relationship("GameQuestion", back_populates="game", cascade="all, delete-orphan", order_by="GameQuestion.position")
    submissions = db.relationship("GameSubmission", back_populates="game", cascade="all, delete-orphan")

class GameQuestion(db.Model):
    __tablename__ = "game_questions"
    __table_args__ = (db.UniqueConstraint("game_id", "position", name="uq_game_question_position"), db.UniqueConstraint("game_id", "question_id", name="uq_game_question_id"))
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(36), db.ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    game = db.relationship("Game", back_populates="questions")
    question = db.relationship("Question")

class GameSubmission(db.Model):
    __tablename__ = "game_submissions"
    __table_args__ = (db.UniqueConstraint("game_id", "question_id", name="uq_submission_game_question"),)
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.String(36), db.ForeignKey("games.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    submitted_answer = db.Column(db.String(256), nullable=False)
    normalized_answer = db.Column(db.String(256), nullable=False)
    points_awarded = db.Column(db.Integer, nullable=False, default=0)
    accepted_answer_id = db.Column(db.Integer, db.ForeignKey("accepted_answers.id"), nullable=False)
    receipt_token = db.Column(db.Text, nullable=False, unique=True)
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    game = db.relationship("Game", back_populates="submissions")
    question = db.relationship("Question")
    accepted_answer = db.relationship("AcceptedAnswer")
