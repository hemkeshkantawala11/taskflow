"""The user journey: create, list, complete, delete a task."""


def test_full_task_journey(client):
    created = client.post("/api/tasks", json={"title": "  Write run instructions  "})
    assert created.status_code == 201
    task = created.json()
    assert task["title"] == "Write run instructions"
    assert task["done"] is False

    listed = client.get("/api/tasks").json()
    assert [t["id"] for t in listed] == [task["id"]]

    done = client.patch(f"/api/tasks/{task['id']}", json={"done": True})
    assert done.status_code == 200 and done.json()["done"] is True

    assert client.delete(f"/api/tasks/{task['id']}").status_code == 204
    assert client.get("/api/tasks").json() == []


def test_open_tasks_are_listed_before_done_ones(client):
    a = client.post("/api/tasks", json={"title": "a"}).json()
    b = client.post("/api/tasks", json={"title": "b"}).json()
    client.patch(f"/api/tasks/{b['id']}", json={"done": True})
    ids = [t["id"] for t in client.get("/api/tasks").json()]
    assert ids == [a["id"], b["id"]]


def test_rejects_empty_and_overlong_titles(client):
    assert client.post("/api/tasks", json={"title": ""}).status_code == 422
    assert client.post("/api/tasks", json={"title": "x" * 201}).status_code == 422


def test_missing_task_returns_404(client):
    assert client.patch("/api/tasks/999", json={"done": True}).status_code == 404
    assert client.delete("/api/tasks/999").status_code == 404


def test_index_page_is_served(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "TaskFlow" in res.text
