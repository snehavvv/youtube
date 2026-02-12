import os
import sys

# Add the frontend directory to the Python path so imports like 'from utils' work
frontend_path = os.path.join(os.path.dirname(__file__), "app_frontend")
sys.path.append(frontend_path)

# Execute the actual application code from app_frontend/app.py
entry_point = os.path.join(frontend_path, "app.py")
with open(entry_point, encoding='utf-8') as f:
    exec(f.read())
