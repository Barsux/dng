from flask import Flask
from celery import Celery
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)  # For session management
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:34444/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:34444/0'
    app.config['REDIS_URL'] = 'redis://localhost:34444/0'

    # Initialize Celery
    celery = Celery(
        app.name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)

    return app, celery

app, celery = create_app()

from app import routes 
