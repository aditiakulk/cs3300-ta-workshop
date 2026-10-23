from pathlib import Path

import pytest

import app as app_module
from app import app, tasks


@pytest.fixture
def client():
    """Provide a Flask test client."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_tasks():
    """Reset tasks and identifiers before each test."""
    tasks.clear()
    tasks.extend([
        {"id": 1, "title": "Project-1 Report"},
        {"id": 2, "title": "Project-2 MMFs"}
    ])
    app_module.next_id = 3


def test_index(client):
    """Render the task tracker page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b"Task Tracker" in response.data


def test_get_tasks(client):
    """Return all tasks with the default priority when omitted."""
    response = client.get('/api/tasks')

    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 2
    assert all(task['priority'] == 'Medium' for task in data)


def test_add_task_success(client):
    """Create a task and return its default priority."""
    response = client.post('/api/tasks', json={"title": "Test new task"})

    assert response.status_code == 201
    created_task = response.get_json()
    assert created_task['title'] == "Test new task"
    assert created_task['priority'] == 'Medium'

    get_response = client.get('/api/tasks')
    assert len(get_response.get_json()) == 3
    assert get_response.get_json()[-1]['priority'] == 'Medium'


@pytest.mark.parametrize('priority', ['Low', 'Medium', 'High'])
def test_add_task_with_priority(client, priority):
    """Create a task with each supported priority."""
    response = client.post(
        '/api/tasks',
        json={"title": f"{priority} task", "priority": priority}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == priority

    tasks_response = client.get('/api/tasks')
    assert tasks_response.get_json()[-1]['priority'] == priority


def test_add_task_invalid_priority(client):
    """Reject priorities outside the supported priority values."""
    response = client.post(
        '/api/tasks',
        json={"title": "Invalid task", "priority": "Urgent"}
    )

    assert response.status_code == 400
    assert response.get_json() == {"error": "Invalid priority"}
    assert len(client.get('/api/tasks').get_json()) == 2


def test_add_task_empty_priority_defaults_to_medium(client):
    """Use Medium when the submitted priority is empty."""
    response = client.post(
        '/api/tasks',
        json={"title": "Empty priority task", "priority": ""}
    )

    assert response.status_code == 201
    assert response.get_json()['priority'] == 'Medium'


def test_index_has_priority_selector(client):
    """Expose Low, Medium, and High in the create-task form."""
    response = client.get('/')
    page = response.get_data(as_text=True)

    assert '<select id="task-priority" name="priority">' in page
    assert '<option value="Low">Low</option>' in page
    assert '<option value="Medium" selected>Medium</option>' in page
    assert '<option value="High">High</option>' in page
    assert 'for="task-priority"' in page


def test_frontend_sends_and_displays_priority():
    """Verify frontend code sends and displays task priority values."""
    javascript_path = Path('static/app.js')
    javascript = javascript_path.read_text(encoding='utf-8')

    assert "document.getElementById('task-priority')" in javascript
    assert 'JSON.stringify({ title, priority })' in javascript
    assert "task.priority || 'Medium'" in javascript
    assert 'Priority: ${priority}' in javascript


def test_add_task_missing_title(client):
    """Reject task creation requests without a title."""
    response = client.post('/api/tasks', json={"wrong_key": "value"})
    assert response.status_code == 400
    assert "error" in response.get_json()

    response = client.post('/api/tasks', json={})
    assert response.status_code == 400


def test_delete_task(client):
    """Delete an existing task."""
    response = client.delete('/api/tasks/1')
    assert response.status_code == 200

    get_response = client.get('/api/tasks')
    data = get_response.get_json()
    assert len(data) == 1
    assert data[0]['id'] == 2
