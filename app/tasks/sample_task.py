from app import celery
from app.tasks.base import BaseTask
import time

class SampleTask(BaseTask):
    def run(self, *args, **kwargs):
        print(f"[TASK RUN] SampleTask started with kwargs={kwargs}")
        workflow_id = kwargs.get('workflow_id')
        self.log("Starting sample task")
        total_steps = 10
        
        for i in range(total_steps):
            time.sleep(1)  # Simulate work
            self.log_progress(
                self.task,
                current=i + 1,
                total=total_steps,
                message=f"Processing step {i + 1}",
                workflow_id=workflow_id
            )
        
        self.log("Sample task completed")
        self.log_final_state(self.task, 'COMPLETED', 'Task completed!', workflow_id=workflow_id)
        return {
            'status': 'Task completed!',
            'progress': 100,
            'logs': self.logs
        }

# Create Celery task
@celery.task(bind=True)
def long_running_task(self, previous_result=None, workflow_id=None, **kwargs):
    print(f"[CELERY TASK] long_running_task called with workflow_id={workflow_id}, kwargs={kwargs}")
    task = SampleTask()
    task.task = self  # Set the Celery task instance
    try:
        return task.run(workflow_id=workflow_id, **kwargs)
    except Exception as e:
        task.log_final_state(self, 'FAILED', str(e), workflow_id=workflow_id)
        raise 