import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from app.core.database import get_db
from app.core.openai import get_openai_client
from app.model.chat_models import Base
from main import app


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:15.3") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def db_engine(postgres_container):
    # Construct the database URL from the container's connection details
    db_url = postgres_container.get_connection_url()
    engine = create_engine(db_url)
    # Create tables
    Base.metadata.create_all(engine)
    yield engine
    # Drop tables after tests are done
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """
    Fixture that provides a new database session for each test function.
    The session is rolled back after each test to ensure isolation.
    """
    connection = db_engine.connect()
    transaction = connection.begin()
    session_local = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = session_local()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def override_get_db(db_session):
    """
    Fixture to override the get_db dependency in FastAPI for testing.
    """
    app.dependency_overrides[get_db] = lambda: db_session
    yield
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def openai_client():
    """
    Fixture to get openai client.
    """
    return get_openai_client()

