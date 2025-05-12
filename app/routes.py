from flask import jsonify, render_template, request, redirect, url_for, flash, session
from app import app, celery
from app.tasks.sample_task import long_running_task
from app.tasks.test_conn_task import conn_task
from app.auth import login_required, login_user, logout_user, register_user, get_current_user
from app.database import get_db, Workflow
from datetime import datetime
import json

@app.route('/')
@login_required
def index():
    return render_template('index.html', user=get_current_user())

@app.route('/workflows')
@login_required
def workflows():
    db = get_db()
    user_workflows = db.query(Workflow).filter_by(user_id=session['user_id']).order_by(Workflow.created_at.desc()).all()
    return render_template('workflows.html', workflows=user_workflows, user=get_current_user())

@app.route('/workflow/<int:workflow_id>')
@login_required
def view_workflow(workflow_id):
    db = get_db()
    workflow = db.query(Workflow).filter_by(id=workflow_id, user_id=session['user_id']).first_or_404()
    return render_template('workflow_detail.html', workflow=workflow, user=get_current_user())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if login_user(username, password):
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        
        success, message = register_user(username, password, email)
        if success:
            flash(message, 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/start_tasks', methods=['POST'])
@login_required
def start_tasks():
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
    
    # Start only the first task
    task_ids = []
    task_types = []
    
    if selected_tasks:
        task_type = selected_tasks[0]
        if task_type == 'conn':
            task = conn_task.delay()
        else:  # default to sample task
            task = long_running_task.delay()
        task_ids.append(task.id)
        task_types.append(task_type)
        
        # Update workflow with first task
        workflow.task_ids = task_ids
        workflow.status = 'RUNNING'
        db.commit()
    
    # Store remaining tasks in session for sequential execution
    remaining_tasks = selected_tasks[1:]
    
    # Redirect to execution page with task IDs
    return jsonify({
        "redirect": url_for('execute_tasks', 
                          task_ids=','.join(task_ids), 
                          task_types=','.join(task_types),
                          remaining_tasks=','.join(remaining_tasks),
                          workflow_id=workflow.id)
    })

@app.route('/execute')
@login_required
def execute_tasks():
    task_ids = request.args.get('task_ids', '').split(',')
    task_types = request.args.get('task_types', '').split(',')
    remaining_tasks = request.args.get('remaining_tasks', '').split(',')
    workflow_id = request.args.get('workflow_id')
    
    if not task_ids or not task_types:
        return redirect(url_for('index'))
    
    # Convert lists to JSON strings for the template
    task_ids_json = json.dumps(task_ids)
    task_types_json = json.dumps(task_types)
    remaining_tasks_json = json.dumps(remaining_tasks)
    
    return render_template('execute.html', 
                         task_ids=task_ids_json, 
                         task_types=task_types_json,
                         remaining_tasks=remaining_tasks_json,
                         workflow_id=workflow_id,
                         user=get_current_user())

@app.route('/start_next_task', methods=['POST'])
@login_required
def start_next_task():
    data = request.get_json()
    remaining_tasks = data.get('remaining_tasks', [])
    workflow_id = data.get('workflow_id')
    
    if not remaining_tasks:
        # Update workflow status to completed
        db = get_db()
        workflow = db.query(Workflow).filter_by(id=workflow_id, user_id=session['user_id']).first()
        if workflow:
            workflow.status = 'COMPLETED'
            workflow.completed_at = datetime.utcnow()
            db.commit()
        return jsonify({"error": "No more tasks to execute"}), 400
    
    # Start the next task
    task_type = remaining_tasks[0]
    if task_type == 'conn':
        task = conn_task.delay()
    else:  # default to sample task
        task = long_running_task.delay()
    
    # Update workflow with new task
    db = get_db()
    workflow = db.query(Workflow).filter_by(id=workflow_id, user_id=session['user_id']).first()
    if workflow:
        workflow.task_ids.append(task.id)
        db.commit()
    
    # Update remaining tasks
    remaining_tasks = remaining_tasks[1:]
    
    return jsonify({
        "task_id": task.id,
        "task_type": task_type,
        "remaining_tasks": remaining_tasks
    })

@app.route('/task_status/<task_id>')
@login_required
def task_status(task_id):
    # Try to get the task result from both task types
    task = conn_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        task = long_running_task.AsyncResult(task_id)
    
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'progress': 0,
            'logs': []
        }
    elif task.state == 'PROGRESS':
        response = {
            'state': task.state,
            'progress': task.info.get('progress', 0),
            'message': task.info.get('message', ''),
            'logs': task.info.get('logs', [])
        }
    elif task.state == 'SUCCESS':
        response = {
            'state': task.state,
            'progress': 100,
            'result': task.info,
            'logs': task.info.get('logs', [])
        }
        
        # Update workflow with task result
        db = get_db()
        workflow = db.query(Workflow).filter(
            Workflow.task_ids.contains([task_id]),
            Workflow.user_id == session['user_id']
        ).first()
        
        if workflow:
            if not workflow.task_results:
                workflow.task_results = {}
            workflow.task_results[task_id] = task.info
            db.commit()
    else:
        response = {
            'state': task.state,
            'progress': 0,
            'logs': []
        }
        
        # Update workflow status to failed
        db = get_db()
        workflow = db.query(Workflow).filter(
            Workflow.task_ids.contains([task_id]),
            Workflow.user_id == session['user_id']
        ).first()
        
        if workflow:
            workflow.status = 'FAILED'
            workflow.completed_at = datetime.utcnow()
            db.commit()
    
    return jsonify(response) 