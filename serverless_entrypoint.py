# Google Cloud Functions Entry Point
import sys
import os

# Adapt path for Cloud Functions structure (everything is usually in root or local packages)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_backend.main import app as fastapi_app
from mangum import Mangum

# Helper to wrap FastAPI for serverless platforms (e.g. AWS Lambda, Vercel)
# For Google Cloud Functions with HTTP trigger, you can often just expose the app object 
# if using the Python 3.11+ runtime which supports ASGI/WSGI adapters automatically or via `functions-framework`.

# For DigitalOcean App Platform / Serverless functions, or general Cloud Run conformance:
# We expose the ASGI app.

app = fastapi_app

# If deploying to AWS Lambda, use Mangum
handler = Mangum(app)
