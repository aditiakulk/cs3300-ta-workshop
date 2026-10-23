from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

PRIORITIES = ("Low", "Medium", "High")
DEFAULT_PRIORITY = "Medium"

tasks = [
    {"id": 1, "title": "Project-1 Report", "priority": DEFAULT_PRIORITY},
    {"id": 2, "title": "Project-2 MMFs", "priority": DEFAULT_PRIORITY}
]
next_id = 3


def ensure_task_priority(task):
    """Add the default priority to tasks that do not have one."""
    task.setdefault("priority", DEFAULT_PRIORITY)
    return task


@app.route('/')
def index():
    """Render the task tracker page."""
    return render_template('index.html')


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Return all tasks with their priorities."""
    for task in tasks:
        ensure_task_priority(task)
    return jsonify(tasks)


@app.route('/api/tasks', methods=['POST'])
def add_task():
    """Create a task with a validated priority."""
    global next_id
    data = request.get_json()

    if not data or not data.get('title'):
        return jsonify({"error": "Title is required"}), 400

    priority = data.get('priority') or DEFAULT_PRIORITY
    if priority not in PRIORITIES:
        return jsonify({"error": "Invalid priority"}), 400

    new_task = {
        "id": next_id,
        "title": data['title'],
        "priority": priority
    }
    tasks.append(new_task)
    next_id += 1

    return jsonify(new_task), 201


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task by its identifier."""
    global tasks
    tasks = [t for t in tasks if t['id'] != task_id]
    return jsonify({"result": "success"}), 200


if __name__ == '__main__':
    app.run(debug=True, port=5000)
