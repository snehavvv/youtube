import streamlit as st
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
import os
from utils import get_collection
from datetime import datetime, timedelta
import pandas as pd

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

st.set_page_config(page_title="YouTube Agentic AI", layout="wide")

st.title("📹 YouTube Monitor & Agentic AI Dashboard")

# Sidebar
st.sidebar.header("Configuration")
api_key_input = st.sidebar.text_input("Google API Key", type="password", value=GOOGLE_API_KEY if GOOGLE_API_KEY else "")

selected_model = "gemini-1.5-flash"
if api_key_input:
    genai.configure(api_key=api_key_input)
    try:
        # Fetch available models dynamically
        model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        if model_list:
            # Try to find a good default
            default_ix = 0
            if "models/gemini-1.5-flash" in model_list:
                default_ix = model_list.index("models/gemini-1.5-flash")
            elif "models/gemini-pro" in model_list:
                default_ix = model_list.index("models/gemini-pro")
            
            selected_model = st.sidebar.selectbox("Select Model", model_list, index=default_ix)
    except Exception as e:
         st.sidebar.error(f"Error fetching models: {e}")

if api_key_input and not GOOGLE_API_KEY:
    st.session_state["api_key"] = api_key_input

# --- Tools ---
def get_video_stats(channel_name: str = None):
    """Returns count of videos and simple stats for a channel or all channels."""
    col = get_collection()
    match = {}
    if channel_name:
        match["channel_title"] = {"$regex": channel_name, "$options": "i"}
    
    count = col.count_documents(match)
    return {"count": count, "channel": channel_name if channel_name else "All"}

def count_videos_last_24h(channel_name: str, keyword: str = None):
    """Counts videos published in last 24 hours, optionally filtering by keyword in title/description."""
    col = get_collection()
    
    # Calculate 24h ago
    # Note: upload_date is stored as ISO string.
    since = (datetime.utcnow() - timedelta(hours=24)).isoformat()
    
    query = {"upload_date": {"$gte": since}}
    if channel_name:
        query["channel_title"] = {"$regex": channel_name, "$options": "i"}
    
    if keyword:
        query["$or"] = [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"description": {"$regex": keyword, "$options": "i"}}
        ]
        
    count = col.count_documents(query)
    return {"count": count, "since": since, "channel": channel_name}

def search_related_videos(keyword: str):
    """Searches for videos with keyword in title or description."""
    col = get_collection()
    query = {
        "$or": [
            {"title": {"$regex": keyword, "$options": "i"}},
            {"description": {"$regex": keyword, "$options": "i"}}
        ]
    }
    cursor = col.find(query).limit(5)
    results = []
    for doc in cursor:
        results.append({
            "title": doc.get('title'),
            "channel": doc.get('channel_title'),
            "date": doc.get('upload_date')
        })
    return results

# Tool Registry for Gemini
tools = [get_video_stats, count_videos_last_24h, search_related_videos]

# --- UI Layout ---

# 1. Dashboard Section
st.header("Recent Videos")
if st.button("Refresh Data"):
    col = get_collection()
    recent = list(col.find({}, {"_id": 0}).sort("upload_date", -1).limit(10))
    st.dataframe(pd.DataFrame(recent))

# 2. Chatbot Section
st.header("Agentic AI Chat")
st.markdown("""
Ask questions like:
- "How many videos from markets channel have we saved?"
- "Count videos about USA in ANINEWSIndia channel in the last 24 hours?"
""")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask the AI agent..."):
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # AI Logic
    try:
        if not api_key_input:
            st.error("Please provide Google API Key in sidebar.")
        else:
            # Use selected model
            model = genai.GenerativeModel(selected_model, tools=tools)
            # Enable automatic function calling
            chat = model.start_chat(enable_automatic_function_calling=True)
            
            # Send message which will auto-execute tools if needed
            response = chat.send_message(prompt)
            
            st.chat_message("assistant").markdown(response.text)
            st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"Error: {e}")

