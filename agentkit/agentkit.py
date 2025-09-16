"""The main AgentKit app."""

import reflex as rx
import requests
from typing import List, Tuple


class State(rx.State):
    """The app state."""

    # The chat history.
    chats: List[Tuple[str, str]] = []

    # The current question.
    question: str

    # The selected model.
    model: str = "phi3"

    def set_question(self, question: str):
        """Set the question."""
        self.question = question

    def set_model(self, model: str):
        """Set the model."""
        self.model = model

    async def answer(self):
        """Answer the user's question."""
        if not self.question:
            return

        # Add the question to the chat history
        self.chats.append(("You", self.question))
        yield

        # Call the backend
        try:
            response = requests.post(
                "http://127.0.0.1:8001/chat",
                json={"message": self.question, "model": self.model},
            )
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            answer = data.get("answer", "Sorry, something went wrong.")
        except requests.exceptions.RequestException as e:
            answer = f"Error: {e}"

        # Add the answer to the chat history
        self.chats.append(("Agent", answer))
        self.question = ""
        yield


def qa(question: str, answer: str) -> rx.Component:
    """A question and answer component."""
    return rx.box(
        rx.box(
            rx.text(question, style={"font_weight": "bold"}),
            text_align="right",
        ),
        rx.box(
            rx.text(answer),
            text_align="left",
        ),
        margin_y="1em",
    )


def chat_history() -> rx.Component:
    """The chat history component."""
    return rx.vstack(
        rx.foreach(
            State.chats,
            lambda messages: qa(messages[0], messages[1]),
        ),
    )


def action_bar() -> rx.Component:
    """The action bar to send a question."""
    return rx.hstack(
        rx.select(
            ["phi3", "gemini-1.5-flash"],
            value=State.model,
            on_change=State.set_model,
        ),
        rx.input(
            value=State.question,
            placeholder="Ask a question",
            on_change=State.set_question,
            width="100%",
        ),
        rx.button("Ask", on_click=State.answer),
        align="center",
    )


def index() -> rx.Component:
    """The main app."""
    return rx.container(
        rx.vstack(
            rx.heading("AgentKit", size="9"),
            rx.radio(
                ["phi3", "gemini-1.5-flash"],
                value=State.model,
                on_change=State.set_model,
            ),
            chat_history(),
            action_bar(),
            spacing="5",
            justify="center",
            min_height="85vh",
        ),
        rx.color_mode.button(position="top-right"),
    )


# Add state and page to the app.
app = rx.App()
app.add_page(index)
