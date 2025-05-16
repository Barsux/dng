from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from contextlib import contextmanager
from sqlalchemy import event
from sqlalchemy.ext.mutable import MutableList

# Set DB path to project root or from environment variable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
db_path = os.environ.get('DNG_DB_PATH') or os.path.join(project_root, 'dng_app.db')
print(f"[DB] Using SQLite database at: {db_path}")
print(f"[DB] Real path: {os.path.realpath(db_path)}")
if os.path.exists(db_path):
    print(f"[DB] Inode: {os.stat(db_path).st_ino}")
else:
    print("[DB] File does not exist yet (will be created on first write)")

engine = create_engine(f'sqlite:///{db_path}', echo=True, isolation_level='AUTOCOMMIT')

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationship with workflows
    workflows = relationship('Workflow', back_populates='user')

    def __repr__(self):
        return f'<User {self.username}>'

class Workflow(Base):
    __tablename__ = 'workflows'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    status = Column(String(20), default='PENDING')  # PENDING, RUNNING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Store task information as JSON
    task_types = Column(JSON, nullable=False)  # List of task types
    task_ids = Column(JSON, nullable=False)    # List of task IDs
    task_results = Column(JSON, nullable=True) # Results of completed tasks
    task_statuses = Column(MutableList.as_mutable(JSON), nullable=True, default=list) # List of per-task status dicts
    
    # Relationship with user
    user = relationship('User', back_populates='workflows')

    def __repr__(self):
        return f'<Workflow {self.name} by {self.user.username}>'

# Create all tables
Base.metadata.create_all(engine)

# Create session factory
Session = sessionmaker(bind=engine)

@contextmanager
def get_db():
    """Get database session as a context manager"""
    db = Session()
    try:
        yield db
    finally:
        db.close() 