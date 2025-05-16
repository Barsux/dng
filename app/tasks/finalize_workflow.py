from app import celery
from app.database import get_db, Workflow

def all_tasks_successful(result):
    # If result is a list of results, check for errors
    if isinstance(result, list):
        for r in result:
            if isinstance(r, dict) and r.get('status', '').lower().startswith('task completed'):
                continue
            else:
                return False
        return True
    # If result is a dict, check for error
    if isinstance(result, dict) and result.get('status', '').lower().startswith('task completed'):
        return True
    return False

@celery.task(bind=True)
def finalize_workflow_status(self, previous_result=None, workflow_id=None):
    """Set workflow status to COMPLETED if all tasks succeeded, else FAILED."""
    with get_db() as db:
        workflow = db.query(Workflow).filter_by(id=workflow_id).first()
        if workflow:
            if all_tasks_successful(previous_result):
                workflow.status = 'COMPLETED'
                from datetime import datetime
                workflow.completed_at = datetime.utcnow()
            else:
                workflow.status = 'FAILED'
            db.commit()
    return {'workflow_id': workflow_id, 'final_status': workflow.status} 