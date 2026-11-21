from app.extensions import db

class AcceptedAnswer(db.Model):
    __tablename__ = "accepted_answers"
    __table_args__ = (db.UniqueConstraint("question_id", "normalized", name="uq_answer_question_normalized"),)
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)
    canonical = db.Column(db.String(256), nullable=False)
    normalized = db.Column(db.String(256), nullable=False)
    rarity_tier = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    explanation = db.Column(db.Text)
    source_url = db.Column(db.Text)
    license_name = db.Column(db.String(120))
    question = db.relationship("Question", back_populates="answers")
    aliases = db.relationship("AnswerAlias", back_populates="answer", cascade="all, delete-orphan")

class AnswerAlias(db.Model):
    __tablename__ = "answer_aliases"
    __table_args__ = (db.UniqueConstraint("answer_id", "normalized", name="uq_alias_answer_normalized"),)
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey("accepted_answers.id", ondelete="CASCADE"), nullable=False, index=True)
    alias = db.Column(db.String(256), nullable=False)
    normalized = db.Column(db.String(256), nullable=False, index=True)
    answer = db.relationship("AcceptedAnswer", back_populates="aliases")
