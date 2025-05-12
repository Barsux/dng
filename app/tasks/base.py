from app import celery
import logging
from typing import Dict, Any, Optional
from datetime import datetime

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

    def log_progress(self, task, current: int, total: int, message: Optional[str] = None) -> None:
        """Log progress and update task state"""
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

    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """Override this method in child classes"""
        raise NotImplementedError("Child classes must implement run method") 