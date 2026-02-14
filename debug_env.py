import os
from pathlib import Path
from dotenv import load_dotenv

# Simulate app_backend/database.py logic
print("--- Check app_backend/database.py logic ---")
fake_file = list(Path.cwd().glob('app_backend/database.py'))
if fake_file:
    f = fake_file[0]
    print(f"File: {f}")
    env_path = f.resolve().parent.parent / '.env'
    print(f"Calculated env path: {env_path}")
    print(f"Env path exists: {env_path.exists()}")
    
    load_dotenv(dotenv_path=env_path)
    uri = os.getenv("MONGO_URI")
    print(f"MONGO_URI: {uri}")
else:
    print("Could not find app_backend/database.py to simulate")

# Simulate scripts/query_db.py logic
print("\n--- Check scripts/query_db.py logic ---")
fake_file_q = list(Path.cwd().glob('scripts/query_db.py'))
if fake_file_q:
    f = fake_file_q[0]
    print(f"File: {f}")
    env_path = f.resolve().parent.parent / '.env'
    print(f"Calculated env path: {env_path}")
    print(f"Env path exists: {env_path.exists()}")
else:
     print("Could not find scripts/query_db.py")

