from app.extensions import db

class DailyChallenge(db.Model):
    __tablename__ = "daily_challenges"
    challenge_date = db.Column(db.Date, primary_key=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, server_default=db.func.now())
    questions = db.relationship("DailyChallengeQuestion", back_populates="challenge", cascade="all, delete-orphan", order_by="DailyChallengeQuestion.position")

class DailyChallengeQuestion(db.Model):
    __tablename__ = "daily_challenge_questions"
    __table_args__ = (
        db.UniqueConstraint("challenge_date", "position", name="uq_daily_question_position"),
        db.UniqueConstraint("challenge_date", "question_id", name="uq_daily_question_id"),
    )
    id = db.Column(db.Integer, primary_key=True)
    challenge_date = db.Column(db.Date, db.ForeignKey("daily_challenges.challenge_date", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    position = db.Column(db.Integer, nullable=False)
    challenge = db.relationship("DailyChallenge", back_populates="questions")
    question = db.relationship("Question")
