class TaskExecutor {
    constructor(taskIds, taskTypes, remainingTasks) {
        this.taskIds = taskIds;
        this.taskTypes = taskTypes;
        this.remainingTasks = remainingTasks;
        this.currentTaskIndex = 0;
        this.taskContainer = $('#taskContainer');
        this.eventSource = null;
    }

    createTaskCard(taskId, taskType) {
        const taskCard = $(`
            <div class="task-card" id="task-${taskId}">
                <div class="task-header">
                    <h3>${taskType} Task</h3>
                    <button class="toggle-logs" data-task-id="${taskId}">Show Logs</button>
                </div>
                <div class="task-content">
                    <div class="progress">
                        <span class="progress-bar" style="width: 0%"></span>
                    </div>
                    <p class="status">Initializing...</p>
                    <div class="log-container" id="logs-${taskId}" style="display:none;">
                        <div class="log-entries"></div>
                    </div>
                </div>
            </div>
        `);

        this.taskContainer.append(taskCard);
        return taskCard;
    }

    toggleLogs(taskId) {
        const logContainer = $(`#logs-${taskId}`);
        const button = $(`#task-${taskId}`).find('.toggle-logs');
        
        if (logContainer.is(':hidden')) {
            logContainer.show();
            button.text('Hide Logs');
        } else {
            logContainer.hide();
            button.text('Show Logs');
        }
    }

    updateLogs(taskId, logs) {
        const logContainer = $(`#logs-${taskId} .log-entries`);
        logContainer.html(logs.map(log => 
            `<div class="log-entry">${log}</div>`
        ).join(''));
        logContainer.scrollTop(logContainer[0].scrollHeight);
    }

    startNextTask() {
        if (this.remainingTasks.length === 0) {
            if (this.eventSource) {
                this.eventSource.close();
            }
            return;
        }

        $.ajax({
            url: '/start_next_task',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                remaining_tasks: this.remainingTasks
            })
        })
        .done(data => {
            this.taskIds.push(data.task_id);
            this.taskTypes.push(data.task_type);
            this.remainingTasks = data.remaining_tasks;
            this.createTaskCard(data.task_id, data.task_type);
        })
        .fail(error => {
            console.error('Failed to start next task:', error);
        });
    }

    handleSSE() {
        this.eventSource = new EventSource("/stream");

        this.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            const taskId = data.task_id;

            const taskCard = $(`#task-${taskId}`);
            if (taskCard.length === 0) return;

            const progressBar = taskCard.find('.progress-bar');
            const statusText = taskCard.find('.status');

            progressBar.css('width', `${data.progress}%`);
            let statusMessage = `Task state: ${data.state}, Progress: ${data.progress}%`;
            if (data.message) {
                statusMessage += ` - ${data.message}`;
            }
            statusText.text(statusMessage);

            if (data.logs) {
                this.updateLogs(taskId, data.logs);
            }

            if (data.state === 'SUCCESS' || data.state === 'FAILURE') {
                this.startNextTask();
            }
        };

        this.eventSource.onerror = (e) => {
            console.error('SSE connection error:', e);
        };
    }

    start() {
        if (this.taskIds.length > 0) {
            const taskId = this.taskIds[0];
            const taskType = this.taskTypes[0];
            this.createTaskCard(taskId, taskType);
        }
        this.handleSSE();
    }
}

// Initialize when document is ready
$(document).ready(() => {
    const taskIds = JSON.parse($('#taskIds').val());
    const taskTypes = JSON.parse($('#taskTypes').val());
    const remainingTasks = JSON.parse($('#remainingTasks').val());
    
    const executor = new TaskExecutor(taskIds, taskTypes, remainingTasks);
    executor.start();

    // Event delegation for toggle logs buttons
    $(document).on('click', '.toggle-logs', function() {
        const taskId = $(this).data('task-id');
        executor.toggleLogs(taskId);
    });
});
