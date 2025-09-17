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

    # The selected model type (phi3 or gemini).
    model_type: str = "phi3"

    # The selected Gemini variant.
    gemini_variant: str = "gemini-2.0-flash-exp"

    def set_question(self, question: str):
        """Set the question."""
        self.question = question

    def set_model_type(self, model_type: str):
        """Set the model type."""
        self.model_type = model_type

    def set_gemini_variant(self, variant: str):
        """Set the Gemini variant."""
        self.gemini_variant = variant

    @property
    def current_model(self) -> str:
        """Get the current model for API calls."""
        if self.model_type == "phi3":
            return "phi3"
        else:
            return self.gemini_variant

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
                json={"message": self.question, "model": self.current_model},
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


def model_selection() -> rx.Component:
    """The model selection component with radio buttons and Gemini dropdown."""
    return rx.vstack(
        rx.heading("Select Model", size="4", margin_bottom="2"),
        rx.radio(
            ["phi3", "Gemini"],
            value=State.model_type,
            on_change=State.set_model_type,
            direction="row",
            spacing="4",
        ),
        rx.cond(
            State.model_type == "Gemini",
            rx.vstack(
                rx.text("Choose Gemini variant:", size="2", margin_top="2"),
                rx.select(
                    [
                        "gemini-2.0-flash-exp",
                        "gemini-2.0-flash-thinking-exp",
                        "gemini-1.5-flash",
                        "gemini-1.5-pro",
                    ],
                    value=State.gemini_variant,
                    on_change=State.set_gemini_variant,
                    width="200px",
                ),
                spacing="2",
            ),
        ),
        spacing="3",
        align="start",
        padding="4",
        border="1px solid gray",
        border_radius="8px",
        margin_bottom="4",
    )


def action_bar() -> rx.Component:
    """The action bar to send a question."""
    return rx.hstack(
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
            model_selection(),
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
