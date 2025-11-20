"""Pytest configuration and fixtures for E2E testing"""

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from api_app.config import settings
from api_app.database import Base
from api_app.main import app


@pytest.fixture(scope="session")
def test_db_engine():
    """Create a test database engine"""
    # Use the same database but we'll use transactions for isolation
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )

    # Create all tables
    Base.metadata.create_all(bind=engine)

    yield engine

    # Drop all tables after tests complete
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a new database session for each test with transaction rollback"""
    connection = test_db_engine.connect()

    # Start a nested transaction
    transaction = connection.begin()

    # Create session bound to this connection
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = session_local()

    yield session

    # Rollback the transaction (cleanup test data)
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def test_client(test_db_session: Session) -> TestClient:
    """Create a FastAPI test client with test database session"""

    def override_get_db() -> Generator[Session, None, None]:
        yield test_db_session

    from api_app.database import get_db

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client

    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def rabbitmq_config():
    """RabbitMQ connection configuration"""
    return {
        "host": os.getenv("RABBIT_HOST", "localhost"),
        "port": int(os.getenv("RABBIT_PORT", 5672)),
        "queue_name": os.getenv("QUEUE_NAME", "weather"),
    }


@pytest.fixture
def postgres_config():
    """PostgreSQL connection configuration"""
    return {
        "host": settings.POSTGRES_HOST,
        "port": settings.POSTGRES_PORT,
        "user": settings.POSTGRES_USER,
        "password": settings.POSTGRES_PASSWORD,
        "db": settings.POSTGRES_DB,
    }


@pytest.fixture
def api_url():
    """API base URL for E2E tests"""
    return os.getenv("API_URL", "http://localhost:8000")


@pytest.fixture
def metabase_url():
    """Metabase URL for health checks"""
    return os.getenv("METABASE_URL", "http://localhost:3000")
