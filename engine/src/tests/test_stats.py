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

pipeline_1 = {
  "name": "pipeline-1",
  "summary": "string",
  "description": "string",
  "services": []
}

task_1 = {
    "service_id": None,
    "data_in": [
        "http://test-service-1.local/test_in",
    ],
    "data_out": [
        "http://test-service-1.local/test_out",
    ]
}

task_2 = {
    "service_id": None,
    "data_in": [
        "http://test-service-2.local/test_in",
    ],
    "data_out": [
        "http://test-service-2.local/test_out",
    ]
}


def test_stats_empty(client: TestClient):
    stats_response = client.get("/stats")
    stats_response_data = stats_response.json()

    assert stats_response.status_code == 200
    assert stats_response_data["tasks"]["total"] == 0
    assert len(stats_response_data["services"]) == 0
    assert len(stats_response_data["pipelines"]) == 0


def test_stats(client: TestClient):
    service_response_1 = client.post("/services", json=service_1)
    service_response_2 = client.post("/services", json=service_2)
    pipeline_1["services"] = []
    pipeline_1["services"].append(service_response_1.json()["id"])
    pipeline_1["services"].append(service_response_2.json()["id"])

    pipeline_response = client.post("/pipelines", json=pipeline_1)

    task_1["service_id"] = service_response_1.json()["id"]
    task_2["service_id"] = service_response_2.json()["id"]
    task_2["pipeline_id"] = pipeline_response.json()["id"]

    client.post("/tasks", json=task_1)
    task_response = client.post("/tasks", json=task_2)
    client.patch(f'/tasks/{task_response.json()["id"]}', json={"status": "finished"})

    stats_response = client.get("/stats")
    stats_response_data = stats_response.json()

    assert pipeline_response.status_code == 200
    assert stats_response_data["tasks"]["total"] == 2
    assert stats_response_data["tasks"]["finished"] == 1
    assert stats_response_data["tasks"]["pending"] == 1
    assert len(stats_response_data["services"]) == 1
    assert len(stats_response_data["pipelines"]) == 1
    assert stats_response_data["services"][service_1["name"]] == 1
    assert stats_response_data["pipelines"][pipeline_1["name"]] == 1

    client.post("/tasks", json=task_1)
    task_response = client.post("/tasks", json=task_2)
    client.patch(f'/tasks/{task_response.json()["id"]}', json={"status": "running"})

    stats_response = client.get("/stats")
    stats_response_data = stats_response.json()

    assert stats_response_data["tasks"]["total"] == 4
    assert stats_response_data["tasks"]["finished"] == 1
    assert stats_response_data["tasks"]["pending"] == 2
    assert stats_response_data["tasks"]["running"] == 1
    assert len(stats_response_data["services"]) == 1
    assert len(stats_response_data["pipelines"]) == 1
    assert stats_response_data["services"][service_1["name"]] == 2
    assert stats_response_data["pipelines"][pipeline_1["name"]] == 2

    client.patch(f'/tasks/{task_response.json()["id"]}', json={"status": "error"})

    stats_response = client.get("/stats")
    stats_response_data = stats_response.json()

    assert stats_response_data["tasks"]["total"] == 4
    assert stats_response_data["tasks"]["finished"] == 1
    assert stats_response_data["tasks"]["pending"] == 2
    assert stats_response_data["tasks"]["error"] == 1
    assert len(stats_response_data["services"]) == 1
    assert len(stats_response_data["pipelines"]) == 1
    assert stats_response_data["services"][service_1["name"]] == 2
    assert stats_response_data["pipelines"][pipeline_1["name"]] == 2

    client.patch(f'/tasks/{task_response.json()["id"]}', json={"status": "unavailable"})

    stats_response = client.get("/stats")
    stats_response_data = stats_response.json()

    assert stats_response_data["tasks"]["total"] == 4
    assert stats_response_data["tasks"]["finished"] == 1
    assert stats_response_data["tasks"]["pending"] == 2
    assert stats_response_data["tasks"]["unavailable"] == 1
    assert len(stats_response_data["services"]) == 1
    assert len(stats_response_data["pipelines"]) == 1
    assert stats_response_data["services"][service_1["name"]] == 2
    assert stats_response_data["pipelines"][pipeline_1["name"]] == 2
