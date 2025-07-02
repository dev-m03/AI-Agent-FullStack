import streamlit as st
import requests

st.title("TailorTalk AI")
st.write("Chat with your calendar assistant!")

if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.history:
    role, content = msg
    st.chat_message(role).write(content)

user_input = st.chat_input("Ask me anything...")

if user_input:
    st.session_state.history.append(("user", user_input))
    response = requests.post("http://localhost:8000/chat", json={"message": user_input})
    reply = response.json()["response"]
    st.session_state.history.append(("assistant", reply))
    st.chat_message("assistant").write(reply)
