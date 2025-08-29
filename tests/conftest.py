import pytest
from app import create_app
from app.models.database import db

@pytest.fixture
def client():
    """
    Provides a test client with an in-memory database.
    Used by all tests to simulate requests.
    """
    app = create_app()
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False

    with app.app_context():
        db.create_all()
        yield app.test_client()   # this is what tests use
        db.session.remove()
        db.drop_all()
