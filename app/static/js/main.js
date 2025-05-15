$(document).ready(function() {
    checkAuthStatus();

    // Event Handlers
    $('#login').on('submit', handleLogin);
    $('#register').on('submit', handleRegister);
    $('#logoutBtn').on('click', handleLogout);
    $('#startTasks').on('click', startTasks);
    $('#showRegister').on('click', function(e) {
        e.preventDefault();
        $('#loginForm').addClass('d-none');
        $('#registerForm').removeClass('d-none');
    });
    $('#showLogin').on('click', function(e) {
        e.preventDefault();
        $('#registerForm').addClass('d-none');
        $('#loginForm').removeClass('d-none');
    });

    // Check authentication status and show appropriate content
    function checkAuthStatus() {
        $.get('/api/auth/status')
            .done(function(response) {
                if (response.authenticated) {
                    showMainContent(response.username);
                    loadWorkflows();
                } else {
                    showLoginForm();
                }
            })
            .fail(function() {
                showLoginForm();
            });
    }

    function showLoginForm() {
        $('#authForms').removeClass('d-none');
        $('#loginForm').removeClass('d-none');
        $('#registerForm').addClass('d-none');
        $('#mainContent').addClass('d-none');
    }

    function showMainContent(username) {
        $('#username').text(username);
        $('#authForms').addClass('d-none');
        $('#mainContent').removeClass('d-none');
    }

    function handleLogin(e) {
        e.preventDefault();
        const formData = {
            username: $('#login input[name="username"]').val(),
            password: $('#login input[name="password"]').val()
        };

        $.ajax({
            url: '/api/auth/login',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                showMainContent(response.username);
                loadWorkflows();
            },
            error: function(xhr) {
                alert(xhr.responseJSON?.error || 'Login failed');
            }
        });
    }

    function handleRegister(e) {
        e.preventDefault();
        const formData = {
            username: $('#register input[name="username"]').val(),
            email: $('#register input[name="email"]').val(),
            password: $('#register input[name="password"]').val()
        };

        $.ajax({
            url: '/api/auth/register',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(formData),
            success: function(response) {
                alert('Registration successful! Please login.');
                $('#register')[0].reset();
                $('#showLogin').click();
            },
            error: function(xhr) {
                alert(xhr.responseJSON?.error || 'Registration failed');
            }
        });
    }

    function handleLogout() {
        $.ajax({
            url: '/api/auth/logout',
            type: 'POST',
            contentType: 'application/json',
            success: function() {
                showLoginForm();
            }
        });
    }

    function startTasks() {
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
                $('#taskProgress').removeClass('d-none');
                monitorWorkflow(response.workflow_id);
                loadWorkflows();
            },
            error: function(xhr) {
                alert(xhr.responseJSON?.error || 'Failed to start tasks');
            }
        });
    }

    function monitorWorkflow(workflowId) {
        const progressBar = $('.progress-bar');
        const taskLogs = $('#taskLogs');

        function updateProgress() {
            $.get(`/api/workflows/${workflowId}/status`)
                .done(function(response) {
                    progressBar.css('width', `${response.progress}%`);
                    progressBar.text(`${response.progress}%`);

                    // Update logs
                    if (response.logs && response.logs.length > 0) {
                        taskLogs.html(response.logs.join('<br>'));
                        taskLogs.scrollTop(taskLogs[0].scrollHeight);
                    }

                    if (response.state === 'SUCCESS') {
                        loadWorkflows();
                    } else if (response.state !== 'FAILURE') {
                        setTimeout(updateProgress, 1000);
                    }
                })
                .fail(function() {
                    alert('Failed to fetch workflow status');
                });
        }

        updateProgress();
    }

    function loadWorkflows() {
        $.get('/api/workflows')
            .done(function(response) {
                const workflowsList = $('#workflowsList');
                workflowsList.empty();

                response.workflows.forEach(function(workflow) {
                    const item = $(`
                        <div class="list-group-item">
                            <h5>${workflow.name}</h5>
                            <p>Status: ${workflow.status}</p>
                            <p>Created: ${new Date(workflow.created_at).toLocaleString()}</p>
                            ${workflow.completed_at ? `<p>Completed: ${new Date(workflow.completed_at).toLocaleString()}</p>` : ''}
                        </div>
                    `);
                    workflowsList.append(item);
                });
            })
            .fail(function() {
                alert('Failed to load workflows');
            });
    }
}); 