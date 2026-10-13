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


@pytest.mark.parametrize("payload", [[], [1], "text", 7, True, None])
def test_non_object_bodies_rejected(client, payload):
    pid = make_project(client)
    tid = client.post(f"/api/projects/{pid}/tasks", json={"title": "valid"}).get_json()["id"]
    import json
    for path, method in [("/api/projects", "post"), (f"/api/projects/{pid}/tasks", "post"), (f"/api/tasks/{tid}", "patch")]:
        response = getattr(client, method)(path, data=json.dumps(payload), content_type="application/json")
        assert response.status_code == 400
        assert "error" in response.get_json()


@pytest.mark.parametrize("bad", [None, 5, True, [], {}])
def test_names_and_titles_must_be_strings(client, bad):
    assert client.post("/api/projects", json={"name": bad}).status_code == 400
    pid = make_project(client)
    assert client.post(f"/api/projects/{pid}/tasks", json={"title": bad}).status_code == 400
    tid = client.post(f"/api/projects/{pid}/tasks", json={"title": "valid"}).get_json()["id"]
    assert client.patch(f"/api/tasks/{tid}", json={"title": bad}).status_code == 400
    assert client.get(f"/api/projects/{pid}/tasks").get_json()[0]["title"] == "valid"


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, [], {}, 0, 4])
def test_priority_is_an_actual_integer(client, bad):
    pid = make_project(client)
    assert client.post(f"/api/projects/{pid}/tasks", json={"title": "x", "priority": bad}).status_code == 400
    tid = client.post(f"/api/projects/{pid}/tasks", json={"title": "valid"}).get_json()["id"]
    assert client.patch(f"/api/tasks/{tid}", json={"priority": bad}).status_code == 400


@pytest.mark.parametrize("bad", [True, 20260101, [], {}, "2026-02-30"])
def test_invalid_due_date_types_rejected(client, bad):
    pid = make_project(client)
    assert client.post(f"/api/projects/{pid}/tasks", json={"title": "x", "due_date": bad}).status_code == 400


@pytest.mark.parametrize("bad", [None, [], {}, True, "invalid"])
def test_invalid_status_types_rejected(client, bad):
    pid = make_project(client)
    tid = client.post(f"/api/projects/{pid}/tasks", json={"title": "valid"}).get_json()["id"]
    assert client.patch(f"/api/tasks/{tid}", json={"status": bad}).status_code == 400


def test_malformed_json_does_not_write(client):
    assert client.post("/api/projects", data='{bad', content_type="application/json").status_code == 400
    assert client.get("/api/projects").get_json() == []
