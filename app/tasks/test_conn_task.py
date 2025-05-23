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
        
        # Use dynamic connection params
        hostname = kwargs.get('host', 'm.barsux.moscow').strip().replace('\n', '')
        port = int(kwargs.get('port', 22))
        username = kwargs.get('username', 'barsux2').strip().replace('\n', '')
        password = kwargs.get('password', 'Harabali2004').strip().replace('\n', '')
        self.client.connect(
            hostname=hostname,
            port=port,
            username=username,
            password=password
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
        self.log_final_state(self.task, 'COMPLETED', 'Task completed!', workflow_id=workflow_id)
        return {
            'status': 'Task completed!',
            'progress': 100,
            'logs': self.logs
        }

# Create Celery task
@celery.task(bind=True)
def conn_task(self, previous_result=None, workflow_id=None, **kwargs):
    print(f"[CELERY TASK] conn_task called with workflow_id={workflow_id}, kwargs={kwargs}")
    task = TestConnTask()
    task.task = self  # Set the Celery task instance
    try:
        return task.run(workflow_id=workflow_id, **kwargs)
    except Exception as e:
        task.log_final_state(self, 'FAILED', str(e), workflow_id=workflow_id)
        raise
        
        
