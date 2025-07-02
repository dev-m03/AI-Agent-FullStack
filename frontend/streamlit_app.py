import os
import requests
import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/chat")


st.set_page_config(page_title="TailorTalk AI", layout="centered")
st.title("🧵 TailorTalk AI Assistant")
st.markdown("Chat with your calendar. Schedule meetings using natural language!")


user_input = st.text_input("💬 Enter your request:", placeholder="e.g. Schedule a meeting tomorrow at 9 PM")


if st.button("Ask TailorTalk") and user_input.strip():
    try:
        with st.spinner("Talking to TailorTalk..."):
            response = requests.post(BACKEND_URL, json={"message": user_input})
            if response.status_code == 200:
                output = response.json().get("output", "✅ Request completed.")
                st.success(output)
            else:
                st.error(f"❌ Error {response.status_code}: {response.text}")
    except Exception as e:
        st.error(f"❌ Could not connect to backend: {e}")
