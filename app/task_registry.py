# Task group and task registry for workflow system
# Each group has fields that apply to the whole group, not individual tasks

TASK_DEFINITIONS = {
    "conn": {
        "id": "conn",
        "name": "SSH Connection Task",
        "description": "Connects to a server via SSH and runs a command."
    },
    "long_running_task": {
        "id": "long_running_task",
        "name": "Sample Long Task",
        "description": "A sample task that runs for a while."
    }
}

TASK_GROUPS = [
    {
        "id": "ssh_ops",
        "name": "SSH Operations",
        "description": "Tasks for SSH server management",
        "tasks": ["conn", "long_running_task"],
        "fields": [
            {"name": "host", "type": "text", "label": "Hostname"},
            {"name": "port", "type": "text", "label": "Port"},
            {"name": "username", "type": "text", "label": "Username"},
            {"name": "password", "type": "password", "label": "Password"},
            {"name": "operation", "type": "select", "label": "Operation", "options": ["ls", "df", "uptime"]}
        ]
    },
    {
        "id": "simple",
        "name": "Simple Tasks",
        "description": "Basic sample tasks",
        "tasks": ["long_running_task"],
        "fields": [
            {"name": "note", "type": "text", "label": "Note"}
        ]
    }
] 