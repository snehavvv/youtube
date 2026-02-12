# Youtube Data Engineering & Agentic AI Pipeline

## Architecture
The system consists of three main components:
1. **Ingestion Script**: Python script using `yt-dlp` to fetch initial historical data (Last 1000 videos).
2. **Backend API (FastAPI)**:
   - Handles YouTube PubSubHubbub Webhook for real-time notifications.
   - Updates MongoDB database upon new video publication.
   - Provides a secure REST API to query recent videos.
3. **Frontend Dashboard (Streamlit)**:
   - Displays recent data.
   - Agentic AI Chatbot powered by Google Gemini (via `google-generativeai`) to answer natural language queries about the data.

## Setup Instructions

### Prerequisites
- Python 3.9+
- MongoDB instance (Local or Atlas)
- Google API Key (for Gemini)

### Installation
1. backend:
   ```bash
   cd app_backend
   pip install -r requirements.txt
   ```
2. frontend:
   ```bash
   cd app_frontend
   pip install -r requirements.txt
   ```
3. scripts:
   Ensure `yt-dlp` is installed (included in backend requirements, or install separately).

### Configuration
Create a `.env` file or set environment variables:
- `MONGO_URI`: Connection string for MongoDB.
- `DB_NAME`: Database name.
- `API_KEY`: Secret key for securing the REST API.
- `GOOGLE_API_KEY`: API Key for Google Gemini.

### Running the System

1. **Initial Data Load**:
   ```bash
   python scripts/ingest.py
   ```

2. **Start Backend Server**:
   ```bash
   cd app_backend
   uvicorn main:app --reload --port 8000
   ```
   - The API will be available at `http://localhost:8000`.
   - Webhook URL: `http://<your-public-ip>/webhook`
   - Secure Endpoint: `GET /videos/recent` (Header `X-API-Key: <your-key>`)

3. **Start Frontend Dashboard**:
   ```bash
   cd app_frontend
   streamlit run app.py
   ```

## Agentic AI Capabilities
The Chatbot uses Google Gemini with function calling tools:
- `get_video_stats`: Counts videos by channel.
- `count_videos_last_24h`: Temporal filtering.
- `search_related_videos`: Content search.

## Tech Stack
- **Language**: Python
- **Database**: MongoDB
- **Backend Framework**: FastAPI
- **Frontend**: Streamlit
- **AI**: Google Gemini (google-generativeai)
- **Deployment**: Design allows for serverless deployment (Cloud Run / Functions).

