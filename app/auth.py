from functools import wraps
from flask import session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from .database import get_db, User

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def login_user(username, password):
    with get_db() as db:
        user = db.query(User).filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['username'] = user.username
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            return True
        return False

def logout_user():
    session.pop('user_id', None)
    session.pop('username', None)

def register_user(username, password, email):
    with get_db() as db:
        # Check if username or email already exists
        if db.query(User).filter_by(username=username).first():
            return False, "Username already exists"
        if db.query(User).filter_by(email=email).first():
            return False, "Email already exists"
        # Create new user
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            email=email
        )
        db.add(user)
        db.commit()
        return True, "User registered successfully"

def get_current_user():
    if 'user_id' not in session:
        return None
    with get_db() as db:
        return db.query(User).get(session['user_id']) 