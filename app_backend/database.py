import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path
import datetime

# Load from .env file explicitly
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Configuration
# Default to a local postgres if not set. User should set this to their Cloud SQL connection string.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/youtube_monitor")

Base = declarative_base()

class Video(Base):
    __tablename__ = 'videos'

    video_id = Column(String, primary_key=True)
    title = Column(String)
    url = Column(String)
    upload_date = Column(DateTime)
    view_count = Column(Integer)
    like_count = Column(Integer)
    description = Column(Text)
    channel_id = Column(String)
    channel_title = Column(String)
    
    # Extra fields for Agentic AI work
    ai_summary = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    transcript = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "video_id": self.video_id,
            "title": self.title,
            "url": self.url,
            "upload_date": self.upload_date.isoformat() if self.upload_date else None,
            "view_count": self.view_count,
            "like_count": self.like_count,
            "description": self.description,
            "channel_id": self.channel_id,
            "channel_title": self.channel_title,
            "ai_summary": self.ai_summary,
            "tags": self.tags
        }

# Create engine
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Create tables
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
