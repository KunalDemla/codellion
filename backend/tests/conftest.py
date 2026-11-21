import pytest
from app import create_app
from app.extensions import db
from app.models import Question
from app.seed import seed_questions

@pytest.fixture()
def app():
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://", "GAME_QUESTION_COUNT": 7})
    with app.app_context():
        db.create_all()
        seed_questions("starter")
        # Keep the first seven starter questions in the fixture for predictable
        # prompt-level tests while production rotates the full bank.
        for question in Question.query.order_by(Question.id).offset(7).all():
            question.status = "draft"
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture()
def client(app):
    return app.test_client()
