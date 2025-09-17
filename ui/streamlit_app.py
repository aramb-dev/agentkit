import streamlit as st
import requests
import sys
import os

# Add the parent directory to Python path so we can import the agent module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.llm_client import llm_client

st.title("AgentKit PoC")

# Get available models from the LLM client
available_models = llm_client.get_available_models()
default_model = llm_client.get_default_model()

# Model selection - use available models or fallback to default
if available_models:
    # Show available models with default selected
    try:
        default_index = available_models.index(default_model)
    except ValueError:
        default_index = 0

    model_choice = st.selectbox(
        "Choose a model:",
        available_models,
        index=default_index,
        help=f"Available Gemini models. Default: {default_model}",
    )
else:
    # Fallback if no models are discovered
    model_choice = st.selectbox(
        "Choose a model:", ["gemini"], help="Using default Gemini model"
    )

# Input for the user's message
user_message = st.text_input("Enter your message:")

if user_message:
    # Make a request to the FastAPI backend
    response = requests.post(
        "http://127.0.0.1:8000/chat",
        json={"message": user_message, "model": model_choice},
    )

    if response.status_code == 200:
        data = response.json()
        st.write("Agent's response:")
        st.write(data["answer"])

    else:
        st.write("Error: Could not get a response from the agent.")
