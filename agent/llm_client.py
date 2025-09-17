"""LLM client for integrating with various AI models."""

from __future__ import annotations

import os
from typing import Optional

from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables from .env file
load_dotenv()


class LLMClient:
    """Client for interacting with language models."""

    def __init__(self):
        self.genai_client: Optional[genai.Client] = None
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize available LLM clients based on environment variables."""
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            try:
                self.genai_client = genai.Client(api_key=google_api_key)
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini client: {e}")

    async def generate_response(self, prompt: str, model: str = "gemini") -> str:
        """Generate a response using the specified model."""
        if model == "gemini" and self.genai_client:
            try:
                response = await self.genai_client.aio.models.generate_content(
                    model='gemini-2.0-flash-001',
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=1000,
                    )
                )
                return response.text if response.text else "No response generated"
            except Exception as e:
                print(f"Error calling Gemini API: {e}")
                return self._fallback_response(prompt)

        # Fallback for when API is not available or model not supported
        return self._fallback_response(prompt)

    async def close(self):
        """Clean up any open connections."""
        # Note: The google-genai client handles connection cleanup automatically
        # This method is provided for future extensibility
        pass

    def _fallback_response(self, prompt: str) -> str:
        """Provide a fallback response when LLM is not available."""
        return (
            "I apologize, but I'm currently unable to access my AI capabilities. "
            "Please check that your API keys are configured correctly. "
            "You can still use my basic tool functions for web search, "
            "document retrieval, and memory operations."
        )

    def is_available(self, model: str = "gemini") -> bool:
        """Check if the specified model is available."""
        if model == "gemini":
            return self.genai_client is not None
        return False


# Global LLM client instance
llm_client = LLMClient()
