import os
import requests
import streamlit as st

st.set_page_config(page_title="TailorTalk AI", page_icon="🧵", layout="centered")

st.markdown("<h1 style='text-align: center;'>🧵 TailorTalk AI Assistant</h1>", unsafe_allow_html=True)
st.markdown("Chat with your calendar. Schedule meetings using natural language!")

user_input = st.text_input("💬 Enter your request:", placeholder="e.g., Schedule a meeting at 10 AM tomorrow")

if st.button("Ask TailorTalk") and user_input.strip():
    with st.spinner("⏳ Thinking..."):
        backend_url = os.getenv("BACKEND_URL")
        if not backend_url:
            st.error("❌ BACKEND_URL environment variable not set.")
        else:
            try:
                response = requests.post(f"{backend_url}/chat", json={"message": user_input})
                if response.status_code == 200:
                    output = response.json().get("output", "✅ Request completed.")
                    st.markdown(output, unsafe_allow_html=True)
                else:
                    st.error(f"❌ Backend error: {response.status_code} - {response.text}")
            except Exception as e:
                st.error(f"❌ Exception: {e}")
