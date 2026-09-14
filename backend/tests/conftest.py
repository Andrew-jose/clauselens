import pytest
from app.core.rate_limit import limiter
from app.db.session import init_db


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Ensure DB is initialized and rate limiter is disabled during test runs."""
    init_db()
    limiter.enabled = False
    yield
    limiter.enabled = True
