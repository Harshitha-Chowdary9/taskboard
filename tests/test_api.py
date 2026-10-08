import pytest
from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({"DATABASE": str(tmp_path / "test.db"), "TESTING": True})
    return app.test_client()


def make_project(client, name="Thesis"):
    return client.post("/api/projects", json={"name": name}).get_json()["id"]


def test_create_and_list_project(client):
    pid = make_project(client)
    projects = client.get("/api/projects").get_json()
    assert projects == [{"id": pid, "name": "Thesis", "total": 0, "done": 0}]


def test_duplicate_project_rejected(client):
    make_project(client)
    assert client.post("/api/projects", json={"name": "Thesis"}).status_code == 409


def test_task_lifecycle(client):
    pid = make_project(client)
    r = client.post(f"/api/projects/{pid}/tasks", json={"title": "Write intro", "priority": 1})
    assert r.status_code == 201
    tid = r.get_json()["id"]
    r = client.patch(f"/api/tasks/{tid}", json={"status": "done"})
    assert r.get_json()["status"] == "done"
    assert client.get("/api/projects").get_json()[0]["done"] == 1
    assert client.delete(f"/api/tasks/{tid}").status_code == 204
    assert client.get(f"/api/projects/{pid}/tasks").get_json() == []


def test_validation(client):
    pid = make_project(client)
    assert client.post(f"/api/projects/{pid}/tasks", json={"title": ""}).status_code == 400
    assert client.post(f"/api/projects/{pid}/tasks", json={"title": "x", "priority": 9}).status_code == 400
    assert client.post(f"/api/projects/{pid}/tasks", json={"title": "x", "due_date": "bad"}).status_code == 400
    assert client.post("/api/projects/99/tasks", json={"title": "x"}).status_code == 404


def test_overdue_flag_and_ordering(client):
    pid = make_project(client)
    client.post(f"/api/projects/{pid}/tasks", json={"title": "low", "priority": 3})
    client.post(f"/api/projects/{pid}/tasks", json={"title": "old", "priority": 1, "due_date": "2000-01-01"})
    tasks = client.get(f"/api/projects/{pid}/tasks").get_json()
    assert [t["title"] for t in tasks] == ["old", "low"]
    assert tasks[0]["overdue"] is True


def test_cascade_delete(client):
    pid = make_project(client)
    client.post(f"/api/projects/{pid}/tasks", json={"title": "a"})
    assert client.delete(f"/api/projects/{pid}").status_code == 204
    assert client.get(f"/api/projects/{pid}/tasks").get_json() == []
