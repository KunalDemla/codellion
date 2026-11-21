from app.extensions import db
class AcceptedAnswer(db.Model):
    __tablename__ = "accepted_answers"
    __table_args__ = (db.UniqueConstraint("question_id", "canonical", name="uq_answer_question_canonical"),)
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    canonical = db.Column(db.String(200), nullable=False)
    normalized = db.Column(db.String(200), nullable=False, index=True)
    rarity_tier = db.Column(db.Integer, nullable=False)
    points = db.Column(db.Integer, nullable=False)
    explanation = db.Column(db.Text)
    source_url = db.Column(db.Text)
    license_name = db.Column(db.String(120))
    question = db.relationship("Question", back_populates="answers")
    aliases = db.relationship("AnswerAlias", back_populates="answer", cascade="all, delete-orphan")

class AnswerAlias(db.Model):
    __tablename__ = "answer_aliases"
    id = db.Column(db.Integer, primary_key=True)
    answer_id = db.Column(db.Integer, db.ForeignKey("accepted_answers.id"), nullable=False)
    alias = db.Column(db.String(200), nullable=False)
    normalized = db.Column(db.String(200), nullable=False, unique=True, index=True)
    answer = db.relationship("AcceptedAnswer", back_populates="aliases")
