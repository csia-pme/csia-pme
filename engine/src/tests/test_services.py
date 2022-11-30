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


service_1 = {
  "name": "service-1",
  "url": "http://test-service-1.local",
  "summary": "string",
  "description": "string",
  "data_in_fields": [
    "string"
  ],
  "data_out_fields": [
    "string"
  ]
}

service_2 = {
  "name": "service-2",
  "url": "http://test-service-2.local",
  "summary": "string",
  "description": "string",
  "data_in_fields": [
    "string"
  ],
  "data_out_fields": [
    "string"
  ]
}


def test_create_service(client: TestClient):
    service_response = client.post("/services", json=service_1)

    assert service_response.status_code == 200


def test_get_service(client: TestClient):
    service_response = client.post("/services", json=service_1)
    service_response_data = service_response.json()

    service_response = client.get(f"/services/{service_response_data['id']}")

    assert service_response.status_code == 200


def test_get_services(client: TestClient):
    client.post("/services/", json=service_1)
    client.post("/services/", json=service_2)

    services_response = client.get("/services")
    services_response_data = services_response.json()

    assert services_response.status_code == 200
    assert len(services_response_data) == 2


def test_delete_service(client: TestClient):
    service_response = client.post("/services", json=service_1)
    service_response_data = service_response.json()

    service_response = client.delete(f"/services/{service_response_data['id']}")

    assert service_response.status_code == 204


def test_update_service(client: TestClient):
    service_response = client.post("/services", json=service_1)
    service_response_data = service_response.json()

    service_response = client.patch(
        f"/services/{service_response_data['id']}",
        json={
            "summary": "new summary"
        }
    )
    service_response_data = service_response.json()

    assert service_response.status_code == 200
    assert service_response_data["updated_at"] != "null"
    assert service_response_data["summary"] == "new summary"


def test_create_service_no_body(client: TestClient):
    response = client.post("/services")

    assert response.status_code == 422


def test_read_service_non_existent(client: TestClient):
    response = client.get("/services/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "Service Not Found"}


def test_delete_service_non_existent(client: TestClient):
    response = client.delete("/services/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "Service Not Found"}


def test_patch_service_non_existent(client: TestClient):
    response = client.patch("/services/00000000-0000-0000-0000-000000000000", json={"status": "running"})

    assert response.status_code == 404
    assert response.json() == {"detail": "Service Not Found"}


def test_read_service_non_processable(client: TestClient):
    response = client.get("/services/bad_id")

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "type_error.uuid"


def test_delete_service_non_processable(client: TestClient):
    response = client.delete("/services/bad_id")

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "type_error.uuid"


def test_patch_service_non_processable(client: TestClient):
    response = client.patch("/services/bad_id", json={"status": "running"})

    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "type_error.uuid"
