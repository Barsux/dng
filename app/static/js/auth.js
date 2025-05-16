$(document).ready(function() {
    // Check if user is already logged in
    checkAuthStatus();

    // Event handlers
    $('#login').on('submit', handleLogin);
    $('#register').on('submit', handleRegister);
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

    // Check authentication status
    function checkAuthStatus() {
        $.get('/api/auth/status')
            .done(function(response) {
                if (response.authenticated) {
                    // If user is authenticated, redirect to tasks page
                    window.location.href = '/tasks';
                }
            });
    }

    // Handle login form submission
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
                // Redirect to tasks page on successful login
                window.location.href = '/tasks';
            },
            error: function(xhr) {
                alert(xhr.responseJSON?.error || 'Login failed');
            }
        });
    }

    // Handle register form submission
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
}); 