from app import celery
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import redis
import json

class BaseTask:
    """Base class for all tasks with common functionality"""
    
    def __init__(self):
        self.logs = []
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)

    def log(self, message: str) -> None:
        """Add a log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp} - {message}"
        self.logs.append(log_entry)
        self.logger.info(message)

    def log_progress(self, task, current: int, total: int, message: Optional[str] = None, workflow_id=None) -> None:
        """Log progress and update task state, and also update workflow DB if workflow_id is provided"""
        progress = (current / total) * 100
        log_message = f"Progress: {progress:.1f}% ({current}/{total})"
        if message:
            log_message += f" - {message}"
        
        self.log(log_message)
        
        task.update_state(
            state='PROGRESS',
            meta={
                'current': current,
                'total': total,
                'progress': progress,
                'message': message,
                'logs': self.logs
            }
        )
        # --- NEW: Write to DB ---
        print(f"[log_progress] Called for task {getattr(task, 'request', None) and task.request.id} with workflow_id={workflow_id}")
        if workflow_id:
            from app.database import get_db, Workflow
            with get_db() as db:
                workflow = db.query(Workflow).filter_by(id=workflow_id).first()
                print(f"[log_progress] Workflow found: {workflow is not None} (id={workflow_id})")
                if workflow:
                    statuses = list(workflow.task_statuses or [])
                    found = False
                    for entry in statuses:
                        if entry['task_id'] == task.request.id:
                            entry.update({
                                'state': 'PROGRESS',
                                'progress': progress,
                                'logs': self.logs,
                                'message': message
                            })
                            found = True
                            break
                    if not found:
                        statuses.append({
                            'task_id': task.request.id,
                            'state': 'PROGRESS',
                            'progress': progress,
                            'logs': self.logs,
                            'message': message
                        })
                    workflow.task_statuses = statuses  # assign new list to ensure commit
                    db.commit()
                    print(f"[log_progress] Updated workflow {workflow_id} in DB with progress {progress}")
        # --- Redis progress reporting ---
        if workflow_id:
            r = redis.Redis(host='localhost', port=34444, db=0)
            r.set(f'workflow:{workflow_id}:progress', json.dumps({
                'task_id': getattr(task, 'request', None) and task.request.id,
                'state': 'PROGRESS',
                'progress': progress,
                'logs': self.logs,
                'message': message
            }))

    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """Override this method in child classes"""
        raise NotImplementedError("Child classes must implement run method")

    def register_task_id(self, workflow_id, task_id):
        from app.database import get_db, Workflow
        with get_db() as db:
            workflow = db.query(Workflow).filter_by(id=workflow_id).first()
            if workflow:
                if task_id not in workflow.task_ids:
                    workflow.task_ids.append(task_id)
                    db.commit() 