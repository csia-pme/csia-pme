import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_session
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_default_route(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200


def test_logger(caplog: pytest.LogCaptureFixture):
    from logger import Logger
    logger = Logger()
    caplog.set_level("INFO")
    logger.info(message="test_info")
    assert "test_info" in caplog.text
    caplog.set_level("WARNING")
    logger.warning(message="test_warning")
    assert "test_warning" in caplog.text
    caplog.set_level("ERROR")
    logger.error(message="test_error")
    assert "test_error" in caplog.text
    caplog.set_level("CRITICAL")
    logger.critical(message="test_critical")
    assert "test_critical" in caplog.text
    caplog.set_level("DEBUG")
    logger.debug(message="test_debug")
    assert "test_debug" in caplog.text


# TODO: update tests when storage is implemented
def test_storage():
    from storage import Storage
    storage = Storage()
    storage.coucou()
