$(document).ready(function() {
    // Check if user is authenticated
    checkAuthStatus();
    
    // Event handlers
    $('#logoutBtn').on('click', handleLogout);

    // Check authentication status
    function checkAuthStatus() {
        $.get('/api/auth/status')
            .done(function(response) {
                if (response.authenticated) {
                    $('#username').text(response.username);
                    // Load workflows list after authentication check
                    loadWorkflows();
                } else {
                    // Redirect to login page if not authenticated
                    window.location.href = '/';
                }
            })
            .fail(function() {
                window.location.href = '/';
            });
    }

    // Load all workflows
    function loadWorkflows() {
        $.get('/api/workflows')
            .done(function(response) {
                const workflowsList = $('#workflowsList');
                workflowsList.empty();

                if (!response.workflows || response.workflows.length === 0) {
                    workflowsList.html(`
                        <div class="text-center py-4">
                            <p class="text-muted">No workflows found.</p>
                            <a href="/tasks" class="btn btn-primary">Create your first workflow</a>
                        </div>
                    `);
                    return;
                }

                // Create table to display workflows
                const table = $(`
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Status</th>
                                    <th>Created</th>
                                    <th>Completed</th>
                                    <th>Tasks</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="workflowsTableBody">
                            </tbody>
                        </table>
                    </div>
                `);
                
                workflowsList.append(table);
                const tableBody = $('#workflowsTableBody');

                // Add each workflow to the table
                response.workflows.forEach(function(workflow) {
                    const row = $(
                        `<tr>
                            <td>${workflow.name}</td>
                            <td><span class="badge ${getStatusBadgeClass(workflow.status)}" style="font-size:1em;">${getStatusBadgeText(workflow.status)}</span></td>
                            <td>${new Date(workflow.created_at).toLocaleString()}</td>
                            <td>${workflow.completed_at ? new Date(workflow.completed_at).toLocaleString() : '-'}</td>
                            <td>${workflow.task_types.join(', ')}</td>
                            <td>
                                <a href="/workflow/${workflow.id}" class="btn btn-sm btn-primary">View</a>
                            </td>
                        </tr>`
                    );
                    tableBody.append(row);
                });
            })
            .fail(function() {
                $('#workflowsList').html('<div class="alert alert-danger">Failed to load workflows</div>');
            });
    }

    // Helper function to get appropriate badge class based on workflow status
    function getStatusBadgeClass(status) {
        switch (status) {
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

    // Helper to get user-friendly badge text with icon
    function getStatusBadgeText(status) {
        switch (status) {
            case 'RUNNING':
                return '<i class="bi bi-arrow-repeat"></i> Running';
            case 'COMPLETED':
                return '<i class="bi bi-check-circle"></i> Completed';
            case 'FAILED':
                return '<i class="bi bi-x-circle"></i> Failed';
            case 'PENDING':
                return '<i class="bi bi-hourglass-split"></i> Pending';
            default:
                return status.charAt(0).toUpperCase() + status.slice(1).toLowerCase();
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