$(document).ready(function() {
    // Check if user is authenticated
    checkAuthStatus();

    // Event handlers
    $('#logoutBtn').on('click', handleLogout);

    // Fetch and render task groups
    fetchTaskGroups();

    function fetchTaskGroups() {
        $.get('/api/task_groups')
            .done(function(response) {
                renderTaskGroups(response.task_groups, response.task_definitions);
            })
            .fail(function() {
                $('#taskGroupsContainer').html('<div class="alert alert-danger">Failed to load task groups</div>');
            });
    }

    function renderTaskGroups(groups, taskDefinitions) {
        const container = $('#taskGroupsContainer');
        container.empty();
        if (!groups || groups.length === 0) {
            container.html('<div class="alert alert-info">No task groups available.</div>');
            return;
        }
        const accordion = $('<div class="accordion" id="taskGroupsAccordion"></div>');
        groups.forEach(function(group, idx) {
            const groupId = `group_${group.id}`;
            // Render task list with checkboxes
            let tasksHtml = '<div class="mb-3"><b>Tasks:</b><div>';
            group.tasks.forEach(function(taskId) {
                const task = taskDefinitions[taskId];
                const fieldId = `taskcb_${group.id}_${taskId}`;
                tasksHtml += `
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" id="${fieldId}" name="task_types" value="${taskId}" checked>
                        <label class="form-check-label" for="${fieldId}">
                            <b>${task ? task.name : taskId}</b>
                            <span class="text-muted" style="font-size:0.95em;">${task && task.description ? task.description : ''}</span>
                        </label>
                    </div>
                `;
            });
            tasksHtml += '</div></div>';
            const card = $(`
                <div class="accordion-item">
                    <h2 class="accordion-header" id="heading_${groupId}">
                        <button class="accordion-button ${idx > 0 ? 'collapsed' : ''}" type="button" data-bs-toggle="collapse" data-bs-target="#collapse_${groupId}" aria-expanded="${idx === 0}" aria-controls="collapse_${groupId}">
                            ${group.name}
                        </button>
                    </h2>
                    <div id="collapse_${groupId}" class="accordion-collapse collapse ${idx === 0 ? 'show' : ''}" aria-labelledby="heading_${groupId}" data-bs-parent="#taskGroupsAccordion">
                        <div class="accordion-body">
                            <div class="mb-2 text-muted">${group.description || ''}</div>
                            <form class="group-form" data-group-id="${group.id}">
                                <div class="group-fields"></div>
                                ${tasksHtml}
                                <button type="submit" class="btn btn-success">Run Workflow</button>
                            </form>
                        </div>
                    </div>
                </div>
            `);
            // Render fields
            const fieldsDiv = card.find('.group-fields');
            group.fields.forEach(function(field) {
                let fieldHtml = '';
                const fieldId = `field_${group.id}_${field.name}`;
                if (field.type === 'text' || field.type === 'password') {
                    fieldHtml = `<div class="mb-3"><label for="${fieldId}" class="form-label">${field.label}</label><input type="${field.type}" class="form-control" id="${fieldId}" name="${field.name}"></div>`;
                } else if (field.type === 'select') {
                    fieldHtml = `<div class="mb-3"><label for="${fieldId}" class="form-label">${field.label}</label><select class="form-select" id="${fieldId}" name="${field.name}">${field.options.map(opt => `<option value="${opt}">${opt}</option>`).join('')}</select></div>`;
                } else if (field.type === 'checkbox') {
                    fieldHtml = `<div class="form-check mb-3"><input class="form-check-input" type="checkbox" id="${fieldId}" name="${field.name}"><label class="form-check-label" for="${fieldId}">${field.label}</label></div>`;
                }
                fieldsDiv.append(fieldHtml);
            });
            // Attach submit handler
            card.find('form.group-form').on('submit', function(e) {
                e.preventDefault();
                const form = $(this);
                const groupId = form.data('group-id');
                const group = groups.find(g => g.id === groupId);
                const groupFields = {};
                group.fields.forEach(function(field) {
                    const fieldElem = form.find(`[name="${field.name}"]`);
                    if (field.type === 'checkbox') {
                        groupFields[field.name] = fieldElem.is(':checked');
                    } else {
                        groupFields[field.name] = fieldElem.val();
                    }
                });
                // Collect selected tasks
                const selectedTasks = [];
                form.find('input[name="task_types"]:checked').each(function() {
                    selectedTasks.push($(this).val());
                });
                if (selectedTasks.length === 0) {
                    alert('Please select at least one task');
                    return;
                }
                // Start workflow with selected tasks and groupFields
                startWorkflow(group, groupFields, selectedTasks);
            });
            accordion.append(card);
        });
        container.append(accordion);
    }

    function startWorkflow(group, groupFields, selectedTasks) {
        $.ajax({
            url: '/api/workflows/start',
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({
                task_types: selectedTasks,
                group_fields: groupFields
            }),
            success: function(response) {
                window.location.href = `/workflow/${response.workflow_id}`;
            },
            error: function(xhr) {
                alert(xhr.responseJSON?.error || 'Failed to start workflow');
            }
        });
    }

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
}); 