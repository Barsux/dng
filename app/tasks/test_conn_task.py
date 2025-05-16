import paramiko
from app import celery
from app.tasks.base import BaseTask
import time

class TestConnTask(BaseTask):
    def run(self, *args, **kwargs):
        print(f"[TASK RUN] TestConnTask started with kwargs={kwargs}")
        workflow_id = kwargs.get('workflow_id')
        total_steps = 5
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.log_progress(
                self.task,
                current=1,
                total=total_steps,
                message=f"Создали профиль подключения.",
                workflow_id=workflow_id
            )
        
        self.client.connect(
            hostname="m.barsux.moscow",
            port=22,
            username="barsux",
            password="Harabali2004"
        )
        time.sleep(5)
        self.log_progress(
                self.task,
                current=2,
                total=total_steps,
                message=f"Подключились к серверу.",
                workflow_id=workflow_id
            )
        out = self.client.exec_command("/bin/ls -latr /")
        self.log_progress(
            self.task,
            current=3,
            total=total_steps,
            message=f"Выполнили команду на сервере.",
            workflow_id=workflow_id
        )
        time.sleep(5)
        stdout = out[1].read().decode()
        self.log_progress(
            self.task,
            current=4,
            total=total_steps,
            message=f"Получили {stdout}",
            workflow_id=workflow_id
        )
        self.client.close()
        self.log_progress(
            self.task,
            current=5,
            total=total_steps,
            message=f"Закрыли соединение.",
            workflow_id=workflow_id
        )
        return {
            'status': 'Task completed!',
            'progress': 100,
            'logs': self.logs
        }

# Create Celery task
@celery.task(bind=True)
def conn_task(self, previous_result=None, workflow_id=None):
    print(f"[CELERY TASK] conn_task called with workflow_id={workflow_id}")
    task = TestConnTask()
    task.task = self  # Set the Celery task instance
    return task.run(workflow_id=workflow_id)
        
        
