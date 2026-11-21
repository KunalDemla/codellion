from app.extensions import db

class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(120), unique=True, nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.Integer, nullable=False, default=1)
    scope = db.Column(db.Text)
    case_sensitive = db.Column(db.Boolean, nullable=False, default=False, server_default=db.false())
    allow_fuzzy = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    status = db.Column(db.String(20), nullable=False, default="approved", index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    category = db.relationship("Category", back_populates="questions")
    answers = db.relationship("AcceptedAnswer", back_populates="question", cascade="all, delete-orphan")
