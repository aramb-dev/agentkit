# AgentKit PoC

This is a proof-of-concept for a simple, modular agent framework called AgentKit.

## Project Structure

- `agent-poc/app/main.py`: FastAPI entrypoint
- `agent-poc/agent/agent.py`: Core agent loop (router + summarizer)
- `agent-poc/agent/router.py`: Logic for choosing tools
- `agent-poc/agent/tools.py`: Fake web/RAG/memory tools
- `agent-poc/agent/prompts.py`: System + summary prompts
- `agent-poc/ui/streamlit_app.py`: Test chat UI
- `requirements.txt`: Project dependencies
- `README.md`: This file

## How to Run

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the FastAPI backend:**
    ```bash
    uvicorn app.main:app --reload --app-dir agent-poc
    ```

3.  **Run the Streamlit UI:**
    ```bash
    streamlit run agent-poc/ui/streamlit_app.py
    ```
