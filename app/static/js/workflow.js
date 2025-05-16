$(document).ready(function() {
    // Check if user is authenticated
    checkAuthStatus();

    // Get workflow ID from URL
    const workflowId = window.location.pathname.split('/').pop();
    
    // Track tasks to maintain individual containers
    const taskContainers = {};
    let taskCount = 0;
    let isPolling = false;
    
    // Event handlers
    $('#logoutBtn').on('click', handleLogout);

    // Check authentication status
    function checkAuthStatus() {
        $.get('/api/auth/status')
            .done(function(response) {
                if (response.authenticated) {
                    $('#username').text(response.username);
                    // Load workflow details after authentication check
                    loadWorkflowDetails();
                    startPolling();
                } else {
                    // Redirect to login page if not authenticated
                    window.location.href = '/';
                }
            })
            .fail(function() {
                window.location.href = '/';
            });
    }

    // Load workflow details
    function loadWorkflowDetails() {
        $.get(`/api/workflows/${workflowId}`)
            .done(function(response) {
                const workflow = response.workflow;
                
                $('#workflowTitle').text(`Workflow: ${workflow.name}`);
                $('#workflowStatus').text(workflow.status);
                $('#workflowCreated').text(`Created: ${new Date(workflow.created_at).toLocaleString()}`);
                
                if (workflow.completed_at) {
                    $('#workflowCompleted').text(`Completed: ${new Date(workflow.completed_at).toLocaleString()}`);
                }
            })
            .fail(function() {
                alert('Failed to load workflow details');
                window.location.href = '/workflows';
            });
    }

    // Start polling for workflow updates
    function startPolling() {
        if (!isPolling) {
            isPolling = true;
            updateWorkflowStatus();
        }
    }

    // Update workflow status
    function updateWorkflowStatus() {
        const tasksContainer = $('#tasksContainer');
        
        $.get(`/api/workflows/${workflowId}/status`)
            .done(function(response) {
                // Remove spinner on first data
                if (tasksContainer.find('.spinner-border').length > 0) {
                    tasksContainer.empty();
                }

                if (!response.tasks || response.tasks.length === 0) {
                    // Show waiting message if no tasks and container is empty
                    if (Object.keys(taskContainers).length === 0) {
                        tasksContainer.html('<div id="waiting-message" class="alert alert-info">Waiting for tasks to start...</div>');
                    }
                } else {
                    // Remove waiting message if it exists
                    $('#waiting-message').remove();
                    
                    // Process each task
                    response.tasks.forEach(function(task, idx) {
                        const taskId = task.task_id || `task-${idx}`;
                        // Create a new container for this task if it doesn't exist
                        if (!taskContainers[taskId]) {
                            taskCount++;
                            const taskNumber = taskCount;
                            
                            const taskDiv = $(
                                `<div class="card mb-3 task-card" id="task-container-${taskId}">
                                    <div class="card-header d-flex justify-content-between align-items-center">
                                        <h5 class="mb-0">Task #${taskNumber}</h5>
                                        <span class="badge task-status-badge" id="task-status-${taskId}">${task.state || 'PENDING'}</span>
                                    </div>
                                    <div class="card-body">
                                        <div class="progress mb-3">
                                            <div class="progress-bar" role="progressbar" 
                                                id="task-progress-${taskId}"
                                                style="width: 0%" 
                                                aria-valuenow="0" 
                                                aria-valuemin="0" 
                                                aria-valuemax="100">0%</div>
                                        </div>
                                        <div class="mb-2">
                                            <strong>Task ID:</strong> <span class="text-muted">${taskId}</span>
                                        </div>
                                        <div class="task-message-container" id="task-message-${taskId}"></div>
                                        <div class="task-logs-container mt-3" id="task-logs-${taskId}"></div>
                                    </div>
                                </div>`
                            );
                            tasksContainer.append(taskDiv);
                            taskContainers[taskId] = {
                                id: taskId,
                                element: taskDiv,
                                number: taskNumber
                            };
                        }
                        // Always update task container with latest data
                        updateTaskContainer(taskId, task);
                    });
                }

                // After updating tasks, check workflow status and stop polling if done
                $.get(`/api/workflows/${workflowId}`)
                    .done(function(wfResp) {
                        const status = wfResp.workflow.status;
                        // Update the workflow status badge
                        const statusBadge = $('#workflowStatus');
                        statusBadge.text(status);
                        statusBadge.removeClass('bg-light text-dark bg-primary bg-success bg-danger bg-secondary bg-info text-white');
                        switch (status) {
                            case 'RUNNING':
                                statusBadge.addClass('bg-primary text-white');
                                break;
                            case 'COMPLETED':
                                statusBadge.addClass('bg-success text-white');
                                break;
                            case 'FAILED':
                                statusBadge.addClass('bg-danger text-white');
                                break;
                            case 'PENDING':
                                statusBadge.addClass('bg-secondary text-white');
                                break;
                            default:
                                statusBadge.addClass('bg-info text-white');
                        }
                        if (status === 'COMPLETED' || status === 'FAILED') {
                            isPolling = false;
                            return; // Do not schedule another poll
                        } else {
                            setTimeout(updateWorkflowStatus, 1000);
                        }
                    })
                    .fail(function() {
                        // If failed to get workflow, try again later
                        setTimeout(updateWorkflowStatus, 3000);
                    });
            })
            .fail(function() {
                console.error('Failed to fetch workflow status');
                if (Object.keys(taskContainers).length === 0) {
                    tasksContainer.html('<div class="alert alert-danger">Failed to fetch workflow status. Retrying...</div>');
                }
                // Try again after failure with a longer timeout
                setTimeout(updateWorkflowStatus, 3000);
            });
    }
    
    // Update individual task container with new data
    function updateTaskContainer(taskId, taskData) {
        // Update task badge status
        const statusBadge = $(`#task-status-${taskId}`);
        statusBadge.text(taskData.state || 'PENDING')
                  .removeClass('bg-primary bg-secondary bg-success bg-danger bg-info')
                  .addClass(getStatusBadgeClass(taskData.state));
        
        // Update progress bar
        const progressBar = $(`#task-progress-${taskId}`);
        const newProgress = parseInt(taskData.progress || 0);
        progressBar.css('width', `${newProgress}%`);
        progressBar.text(`${newProgress}%`);
        progressBar.attr('aria-valuenow', newProgress);
        
        // Update message if present
        const messageContainer = $(`#task-message-${taskId}`);
        if (taskData.message) {
            messageContainer.html(`<div class="mb-2"><strong>Message:</strong> ${taskData.message}</div>`);
        }
        
        // Update logs if present
        const logsContainer = $(`#task-logs-${taskId}`);
        if (taskData.logs && taskData.logs.length) {
            logsContainer.html(`
                <strong>Logs:</strong>
                <div class="logs-container mt-2 p-2 bg-light" style="max-height:150px;overflow-y:auto;font-size:0.8rem;font-family:monospace;">
                    ${taskData.logs.join('<br>')}
                </div>
            `);
        }
    }

    // Helper function to get appropriate badge class based on task state
    function getStatusBadgeClass(state) {
        switch (state) {
            case 'RUNNING':
                return 'bg-primary';
            case 'COMPLETED':
                return 'bg-success';
            case 'FAILED':
                return 'bg-danger';
            case 'PENDING':
                return 'bg-secondary';
            default:
                return 'bg-info';
        }
    }

    // Handle logout
    function handleLogout() {
        $.ajax({
            url: '/api/auth/logout',
            type: 'POST',
            contentType: 'application/json',
            success: function() {
                window.location.href = '/';
            }
        });
    }
}); 