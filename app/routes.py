from flask import jsonify, request, session, abort
from app import app, celery
from app.tasks.sample_task import long_running_task
from app.tasks.test_conn_task import conn_task
from app.auth import login_required, login_user, logout_user, register_user, get_current_user
from app.database import get_db, Workflow
from datetime import datetime
from celery import chain
import os

# Serve static files
@app.route('/')
def index():
    return app.send_static_file('index.html')

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
    db = get_db()
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

@app.route('/api/workflows/start', methods=['POST'])
@login_required
def start_workflow():
    data = request.get_json()
    selected_tasks = data.get('task_types', [])
    
    if not selected_tasks:
        return jsonify({"error": "No tasks selected"}), 400
    
    # Create workflow record
    db = get_db()
    workflow = Workflow(
        user_id=session['user_id'],
        name=f"Workflow {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",
        task_types=selected_tasks,
        task_ids=[],
        status='PENDING'
    )
    db.add(workflow)
    db.commit()
    
    # Create task chain
    task_chain = []
    for task_type in selected_tasks:
        if task_type == 'conn':
            task_chain.append(conn_task.s())
        else:  # default to sample task
            task_chain.append(long_running_task.s())
    
    # Execute chain
    workflow_chain = chain(*task_chain)
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
    db = get_db()
    workflow = db.query(Workflow).filter_by(id=workflow_id, user_id=session['user_id']).first()
    if not workflow:
        abort(404)
    
    if not workflow.task_ids:
        return jsonify({
            'state': 'PENDING',
            'progress': 0,
            'logs': []
        })
    
    # Get the chain result
    chain_id = workflow.task_ids[0]
    result = celery.AsyncResult(chain_id)
    
    if result.ready():
        if result.successful():
            workflow.status = 'COMPLETED'
            workflow.completed_at = datetime.utcnow()
            workflow.task_results = result.get()
            db.commit()
            
            return jsonify({
                'state': 'SUCCESS',
                'progress': 100,
                'result': result.get(),
                'logs': result.get().get('logs', []) if isinstance(result.get(), dict) else []
            })
        else:
            workflow.status = 'FAILED'
            workflow.completed_at = datetime.utcnow()
            db.commit()
            
            return jsonify({
                'state': 'FAILURE',
                'progress': 0,
                'error': str(result.result),
                'logs': []
            })
    
    # For tasks in progress
    if isinstance(result.info, dict):
        progress = result.info.get('progress', 0)
        logs = result.info.get('logs', [])
    else:
        progress = 0
        logs = []
    
    return jsonify({
        'state': result.state,
        'progress': progress,
        'logs': logs
    }) 