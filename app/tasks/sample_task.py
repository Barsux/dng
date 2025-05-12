from app import celery
from app.tasks.base import BaseTask
import time

class SampleTask(BaseTask):
    def run(self, *args, **kwargs):
        self.log("Starting sample task")
        total_steps = 10
        
        for i in range(total_steps):
            time.sleep(1)  # Simulate work
            self.log_progress(
                self.task,
                current=i + 1,
                total=total_steps,
                message=f"Processing step {i + 1}"
            )
        
        self.log("Sample task completed")
        return {
            'status': 'Task completed!',
            'progress': 100,
            'logs': self.logs
        }

# Create Celery task
@celery.task(bind=True)
def long_running_task(self):
    task = SampleTask()
    task.task = self  # Set the Celery task instance
    return task.run() 