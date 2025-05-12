# Flask Task Monitor

A Flask web application that allows running and monitoring long-running tasks using Celery.

## Requirements

- Python 3.6
- Redis server
- Virtual environment (recommended)

## Setup

1. Create and activate a virtual environment:
```bash
python3.6 -m venv venv
source venv/bin/activate  # On Linux/Mac
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Make sure Redis server is running:
```bash
redis-server
```

4. Start Celery worker (in a separate terminal):
```bash
celery -A app.celery worker --loglevel=info
```

5. Run the Flask application:
```bash
python -m flask run
```

## Usage

1. Open your browser and navigate to `http://localhost:5000`
2. Click "Start New Task" to begin a sample task
3. Watch the progress bar and status updates in real-time

## Project Structure

- `app/` - Main application directory
  - `tasks/` - Directory containing task definitions
  - `templates/` - HTML templates
  - `static/` - Static files (CSS, JS)
  - `__init__.py` - Application factory and Celery configuration
  - `routes.py` - Route definitions

## Adding New Tasks

To add new tasks:
1. Create a new Python file in the `app/tasks/` directory
2. Define your task using the `@celery.task` decorator
3. Import and use the task in `routes.py` 