$(document).ready(function() {
    // Check if user is authenticated
    checkAuthStatus();

    // Event handlers
    $('#logoutBtn').on('click', handleLogout);
    $('#startTasks').on('click', startWorkflow);

    // Check authentication status
    function checkAuthStatus() {
        $.get('/api/auth/status')
            .done(function(response) {
                if (response.authenticated) {
                    $('#username').text(response.username);
                } else {
                    // Redirect to login page if not authenticated
                    window.location.href = '/';
                }
            })
            .fail(function() {
                window.location.href = '/';
            });
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

    // Start workflow with selected tasks
    function startWorkflow() {
        const selectedTasks = [];
        $('input[type="checkbox"]:checked').each(function() {
            selectedTasks.push($(this).val());
        });

        if (selectedTasks.length === 0) {
            alert('Please select at least one task');
            return;
        }

        $.ajax({
            url: '/api/workflows/start',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ task_types: selectedTasks }),
            success: function(response) {
                // Redirect to the workflow details page
                window.location.href = `/workflow/${response.workflow_id}`;
            },
            error: function(xhr) {
                alert(xhr.responseJSON?.error || 'Failed to start workflow');
            }
        });
    }
}); 