import pytest
from app.core.rate_limit import limiter
from app.db.session import init_db, SessionLocal


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Ensure DB is initialized and rate limiter is disabled during test runs."""
    init_db()
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.fixture
def db_session():
    """Yields a database session for unit tests."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
