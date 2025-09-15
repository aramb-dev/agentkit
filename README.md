# AgentKit PoC

This is a proof-of-concept for a simple, modular agent framework called AgentKit.

## Project Structure

- `app/main.py`: FastAPI entrypoint
- `agent/agent.py`: Core agent loop (router + summarizer)
- `agent/router.py`: Logic for choosing tools
- `agent/tools.py`: Fake web/RAG/memory tools
- `agent/prompts.py`: System + summary prompts
- `ui/streamlit_app.py`: Test chat UI
- `requirements.txt`: Project dependencies
- `README.md`: This file

## How to Run

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the FastAPI backend:**

    ```bash
    uvicorn app.main:app --reload
    ```

3.  **Run the Streamlit UI:**
    ```bash
    streamlit run ui/streamlit_app.py
    ```
