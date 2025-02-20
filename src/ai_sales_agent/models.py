"""Database models for email tracking and meeting scheduling."""

from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class EmailEvent(Base):
    """Model for tracking email engagement events."""
    __tablename__ = 'email_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, nullable=False)
    event_type = Column(String, nullable=False)  # open, click, bounce, spam_report
    timestamp = Column(DateTime, default=datetime.utcnow)
    metadata = Column(String)  # JSON string for additional event data

class Meeting(Base):
    """Model for scheduled meetings."""
    __tablename__ = 'meetings'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    organizer_email = Column(String, nullable=False)
    attendee_email = Column(String, nullable=False)
    status = Column(String, default='scheduled')  # scheduled, cancelled, completed
    provider = Column(String, nullable=False)  # google_calendar, calendly
    external_id = Column(String)  # ID from external provider
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

def init_db(connection_string: str):
    """Initialize database and create tables.
    
    Args:
        connection_string (str): Database connection string
    """
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    return engine