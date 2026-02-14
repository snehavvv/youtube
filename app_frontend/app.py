import streamlit as st
from dotenv import load_dotenv
load_dotenv()

import google.generativeai as genai
import os
import time
from utils import get_db_session
from datetime import datetime, timedelta
import pandas as pd
from sqlalchemy import text

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
        
        # Filter for stable/flash models which are usually best for free tier
        if model_list:
            default_ix = 0
            # Prioritize 1.5 Flash (highest free tier limits)
            priorities = ["models/gemini-1.5-flash", "models/gemini-1.5-pro", "models/gemini-pro"]
            
            for p in priorities:
                if p in model_list:
                    default_ix = model_list.index(p)
                    break
            
            selected_model = st.sidebar.selectbox(
                "Select Model", 
                model_list, 
                index=default_ix,
                help="Gemini 1.5 Flash is recommended for the Free Tier (higher rate limits)."
            )
            
            if "flash" in selected_model:
                st.sidebar.success("✅ Flash model selected (Good for Free Tier)")
                
    except Exception as e:
         st.sidebar.error(f"Error fetching models: {e}")

if api_key_input and not GOOGLE_API_KEY:
    st.session_state["api_key"] = api_key_input

def get_db_connection():
    return get_db_session()

# --- Tools ---
def get_video_stats(channel_name: str = None):
    """
    Returns count of videos for a specific channel or all channels if not specified.
    Use this tool when users ask 'how many videos' or 'total videos' for a channel.
    """
    print(f"Tool: get_video_stats called for channel={channel_name}")
    session = get_db_session()
    
    if channel_name:
        query_str = "SELECT COUNT(*) FROM videos WHERE channel_title LIKE :channel"
        params = {"channel": f"%{channel_name}%"}
    else:
        query_str = "SELECT COUNT(*) FROM videos"
        params = {}
    
    result = session.execute(text(query_str), params).scalar()
    session.close()
    return f"Total videos found for {channel_name if channel_name else 'all channels'}: {result}"

def count_videos_last_24h(channel_name: str = None, keyword: str = None):
    """
    Counts videos published in last 24 hours. Optional filters: channel_name, keyword.
    Use this for queries like 'recent videos about X', 'videos in last 24h'.
    """
    print(f"Tool: count_videos_last_24h called (channel={channel_name}, keyword={keyword})")
    session = get_db_session()
    since = (datetime.utcnow() - timedelta(hours=24))
    
    query_str = "SELECT COUNT(*) FROM videos WHERE upload_date >= :since"
    params = {"since": since}
    
    if channel_name:
        query_str += " AND channel_title LIKE :channel"
        params["channel"] = f"%{channel_name}%"
    
    if keyword:
        query_str += " AND (title LIKE :keyword OR description LIKE :keyword)"
        params["keyword"] = f"%{keyword}%"
        
    result = session.execute(text(query_str), params).scalar()
    session.close()
    return f"Videos in last 24h" + (f" for channel '{channel_name}'" if channel_name else "") + (f" matching '{keyword}'" if keyword else "") + f": {result}"

def search_videos(keyword: str, days: int = 7):
    """
    Searches for videos matching a keyword in title/description within the last X days (default 7).
    Returns a list of titles and dates.
    Use this when user asks to 'find videos about X' or 'what are the videos regarding Y'.
    """
    print(f"Tool: search_videos called (keyword={keyword})")
    session = get_db_session()
    since = (datetime.utcnow() - timedelta(days=days))
    
    query_str = "SELECT title, channel_title, upload_date FROM videos WHERE upload_date >= :since AND (title LIKE :keyword OR description LIKE :keyword) LIMIT 5"
    params = {"keyword": f"%{keyword}%", "since": since}
    
    result = session.execute(text(query_str), params)
    videos = []
    for row in result:
        videos.append(f"- {row[0]} ({row[1]}) on {row[2]}")
    session.close()
    
    if not videos:
        return "No videos found."
    return "\n".join(videos)

# Tool Registry for Gemini
tools_list = [get_video_stats, count_videos_last_24h, search_videos]

# --- UI Layout ---

# Authentication Check
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def check_password():
    def password_entered():
        if st.session_state["password"] == "admin123": # Simple demo password
            st.session_state.authenticated = True
            del st.session_state["password"]
        else:
            st.session_state.authenticated = False
            st.error("😕 Password incorrect")

    if not st.session_state.authenticated:
        st.text_input("Please enter password to access dashboard:", type="password", on_change=password_entered, key="password")
        return False
    return True

if check_password():
    # 1. Dashboard Section
    st.header("Recent Videos")
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Refresh Data"):
            st.session_state.refresh = True
    
    if st.session_state.get("refresh", False):
        session = get_db_session()
        try:
            result = session.execute(text("SELECT * FROM videos ORDER BY upload_date DESC LIMIT 10"))
            try:
                recent = [dict(row._mapping) for row in result]
            except:
                recent = [dict(row) for row in result]
            st.dataframe(pd.DataFrame(recent))
        finally:
            session.close()

    # 2. Chatbot Section
    st.header("Agentic AI Chat")
    st.markdown("""
    Ask questions like:
    - "How many videos from markets channel have we saved?"
    - "Count videos about USA in ANINEWSIndia channel in the last 24 hours?"
    - "Search for videos about inflation"
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
                with st.spinner('Agent is thinking...'):
                    # Context for the agent
                    session = get_db_session()
                    try:
                        channels = [row[0] for row in session.execute(text("SELECT DISTINCT channel_title FROM videos WHERE channel_title IS NOT NULL")).fetchall()]
                        channel_list_str = ", ".join(channels)
                    except Exception as e:
                        channel_list_str = "Error fetching channel list"
                    finally:
                        session.close()

                    system_instruction = f"You are a helpful YouTube Data Analyst. Use the provided tools to query the database and answer user questions. Always answer based on the tool outputs. The available channels in the database are: {channel_list_str}. If a user asks about a channel, map it to one of these exact names."
                    
                    # Create model with tools
                    model = genai.GenerativeModel(selected_model, tools=tools_list, system_instruction=system_instruction)
                    
                    # Build history for Gemini
                    history = []
                    # Skip the latest message which is the prompt we are about to send via send_message
                    for msg in st.session_state.messages[:-1]: 
                        role = "user" if msg["role"] == "user" else "model"
                        history.append({"role": role, "parts": [msg["content"]]})
                    
                    # Start chat with history
                    chat = model.start_chat(history=history, enable_automatic_function_calling=True)
                    
                    # Send message
                    response = chat.send_message(prompt)
                    
                    if response.text:
                        st.chat_message("assistant").markdown(response.text)
                        st.session_state.messages.append({"role": "assistant", "content": response.text})
                    else:
                        st.chat_message("assistant").markdown("I processed your request but have no text response.")
                        st.session_state.messages.append({"role": "assistant", "content": "I processed your request."})

        except Exception as e:
            st.error(f"Error: {e}")
            if "429" in str(e):
                st.warning("Rate limit exceeded. Please wait a moment.")

