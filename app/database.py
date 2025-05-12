from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Create SQLite database in the app directory
db_path = os.path.join(os.path.dirname(__file__), 'app.db')
engine = create_engine(f'sqlite:///{db_path}', echo=True)
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
    
    # Relationship with user
    user = relationship('User', back_populates='workflows')

    def __repr__(self):
        return f'<Workflow {self.name} by {self.user.username}>'

# Create all tables
Base.metadata.create_all(engine)

# Create session factory
Session = sessionmaker(bind=engine)

def get_db():
    """Get database session"""
    db = Session()
    try:
        return db
    finally:
        db.close() 