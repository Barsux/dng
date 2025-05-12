from flask import Flask
from celery import Celery
from flask_sse import sse
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.urandom(24)  # For session management
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    app.config['REDIS_URL'] = 'redis://localhost:6379/0'
    app.register_blueprint(sse, url_prefix='/stream')

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