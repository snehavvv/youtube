import os
import streamlit as st
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Load from .env file explicitly
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Configuration
# Default to a local postgres if not set. User should set this to their Cloud SQL connection string.
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/youtube_monitor")

def get_db_connection():
    engine = create_engine(DATABASE_URL)
    return engine.connect()

def get_db_session():
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return Session()
