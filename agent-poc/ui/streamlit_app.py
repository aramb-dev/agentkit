import streamlit as st
import requests

st.title("AgentKit PoC")

# Input for the user's message
user_message = st.text_input("Enter your message:")

if user_message:
    # Make a request to the FastAPI backend
    response = requests.post(
        "http://127.0.0.1:8000/chat", json={"message": user_message}
    )

    if response.status_code == 200:
        data = response.json()
        st.write("Agent's response:")
        st.write(data["answer"])
        if data["tool_used"]:
            st.write(f"Tool used: {data['tool_used']}")
    else:
        st.write("Error: Could not get a response from the agent.")
