from flask import jsonify, request, session, abort, send_from_directory
from app import app, celery
from app.tasks.sample_task import long_running_task
from app.tasks.test_conn_task import conn_task
from app.auth import login_required, login_user, logout_user, register_user, get_current_user
from app.database import get_db, Workflow, Session
from datetime import datetime
from celery import chain
import os
import redis
import json
from app.tasks.finalize_workflow import finalize_workflow_status

# Serve static pages
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/tasks')
@login_required
def tasks_page():
    return send_from_directory('static', 'tasks.html')

@app.route('/workflows')
@login_required
def workflows_page():
    return send_from_directory('static', 'workflows.html')

@app.route('/workflow/<int:workflow_id>')
@login_required
def workflow_detail_page(workflow_id):
    return send_from_directory('static', 'workflow.html')

# Authentication endpoints
@app.route('/api/auth/status')
def auth_status():
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'username': get_current_user().username
        })
    return jsonify({'authenticated': False})

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    email = data.get('email')
    
    success, message = register_user(username, password, email)
    if success:
        return jsonify({
            'success': True,
            'message': message
        })
    return jsonify({
        'error': message
    }), 400

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if login_user(username, password):
        return jsonify({
            'success': True,
            'username': username
        })
    return jsonify({'error': 'Invalid username or password'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    logout_user()
    return jsonify({'success': True})

# Workflow endpoints
@app.route('/api/workflows')
@login_required
def get_workflows():
    with get_db() as db:
        user_workflows = db.query(Workflow).filter_by(user_id=session['user_id']).order_by(Workflow.created_at.desc()).all()
        return jsonify({
            'workflows': [{
                'id': w.id,
                'name': w.name,
                'status': w.status,
                'created_at': w.created_at.isoformat(),
                'completed_at': w.completed_at.isoformat() if w.completed_at else None,
                'task_types': w.task_types
            } for w in user_workflows]
        })

@app.route('/api/workflows/<int:workflow_id>')
@login_required
def get_workflow(workflow_id):
    with get_db() as db:
        workflow = db.query(Workflow).filter_by(id=workflow_id, user_id=session['user_id']).first()
        if not workflow:
            return jsonify({'error': 'Workflow not found'}), 404
        
        return jsonify({
            'workflow': {
                'id': workflow.id,
                'name': workflow.name,
                'status': workflow.status,
                'created_at': workflow.created_at.isoformat(),
                'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
                'task_types': workflow.task_types,
                'task_ids': workflow.task_ids
            }
        })

@app.route('/api/workflows/start', methods=['POST'])
@login_required
def start_workflow():
    data = request.get_json()
    selected_tasks = data.get('task_types', [])
    
    if not selected_tasks:
        return jsonify({"error": "No tasks selected"}), 400
    
    with get_db() as db:
        workflow = Workflow(
            user_id=session['user_id'],
            name=f"Workflow {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
            task_types=selected_tasks,
            task_ids=[],
            status='PENDING'
        )
        db.add(workflow)
        db.commit()
        
        # Create task chain, passing workflow_id to each task
        task_chain = []
        for task_type in selected_tasks:
            if task_type == 'conn':
                task_chain.append(conn_task.s(workflow_id=workflow.id))
            else:  # default to sample task
                task_chain.append(long_running_task.s(workflow_id=workflow.id))
        
        # Add finalization task
        from celery import chain as celery_chain
        workflow_chain = celery_chain(*task_chain) | finalize_workflow_status.s(workflow_id=workflow.id)
        result = workflow_chain.apply_async()
        
        # Store chain ID
        workflow.task_ids = [result.id]
        workflow.status = 'RUNNING'
        db.commit()
        
        return jsonify({
            'success': True,
            'workflow_id': workflow.id
        })

@app.route('/api/workflows/<int:workflow_id>/status')
@login_required
def workflow_status(workflow_id):
    r = redis.Redis(host='localhost', port=34444, db=0)
    # Aggregate all per-task progress
    keys = r.keys(f'workflow:{workflow_id}:task:*:progress')
    tasks = []
    total_progress = 0
    for key in keys:
        progress_json = r.get(key)
        if progress_json:
            task_status = json.loads(progress_json)
            tasks.append(task_status)
            total_progress += task_status.get('progress', 0)
    num_tasks = len(tasks)
    overall_progress = int(total_progress / num_tasks) if num_tasks > 0 else 0
    return jsonify({
        'overall_progress': overall_progress,
        'tasks': tasks
    }) 