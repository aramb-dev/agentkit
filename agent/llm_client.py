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
        self.available_models: list[str] = []
        self._initialize_clients()

    def _initialize_clients(self):
        """Initialize available LLM clients based on environment variables."""
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if google_api_key:
            try:
                self.genai_client = genai.Client(api_key=google_api_key)
                # Load available models
                self._load_available_models()
            except Exception as e:
                print(f"Warning: Failed to initialize Gemini client: {e}")
                # Set fallback models even if client init fails
                self._set_fallback_models()
        else:
            print("No Google API key found, using fallback models")
            # Set fallback models when no API key
            self._set_fallback_models()
    
    def _set_fallback_models(self):
        """Set fallback models when API is not available."""
        self.available_models = [
            "gemini-2.0-flash-001",
            "gemini-1.5-flash", 
            "gemini-1.5-pro",
        ]

    def _load_available_models(self):
        """Load available text generation models from Google GenAI."""
        if not self.genai_client:
            return

        try:
            # Get list of available models
            models = list(self.genai_client.models.list())

            # Filter for text generation models
            text_models = []
            for model in models:
                try:
                    model_name = getattr(model, "name", None)
                    if model_name:
                        # Extract just the model name (remove "models/" prefix if present)
                        clean_name = (
                            model_name.replace("models/", "")
                            if model_name.startswith("models/")
                            else model_name
                        )

                        # Include Gemini models (which support text generation)
                        if "gemini" in clean_name.lower():
                            text_models.append(clean_name)
                except Exception:
                    continue  # Skip models that cause errors

            self.available_models = (
                sorted(text_models)
                if text_models
                else ["gemini-2.0-flash-001", "gemini-1.5-flash", "gemini-1.5-pro"]
            )
            print(
                f"Found {len(self.available_models)} available text models: {', '.join(self.available_models[:3])}{'...' if len(self.available_models) > 3 else ''}"
            )

        except Exception as e:
            print(f"Warning: Could not load available models: {e}")
            # Use fallback models
            self._set_fallback_models()

    def get_available_models(self) -> list[str]:
        """Get list of available text generation models."""
        return self.available_models.copy()

    def get_default_model(self) -> str:
        """Get the default/recommended model."""
        if self.available_models:
            # Prefer flash models for speed, then pro models
            for model in self.available_models:
                if "flash" in model.lower():
                    return model
            return self.available_models[0]
        return "gemini-2.0-flash-001"  # Fallback

    async def generate_response(self, prompt: str, model: str = "gemini") -> str:
        """Generate a response using the specified model."""
        if self.genai_client:
            try:
                # Determine which model to use
                if model == "gemini":
                    model_name = self.get_default_model()
                elif model in self.available_models:
                    model_name = model
                else:
                    # If model not found, use default
                    model_name = self.get_default_model()

                response = await self.genai_client.aio.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=4000,
                    ),
                )
                return response.text if response.text else "No response generated"
            except Exception as e:
                print(f"Error calling Gemini API with model {model}: {e}")
                return self._fallback_response(prompt)

        # Fallback for when API is not available
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
        elif model in self.available_models:
            return self.genai_client is not None
        return False


# Global LLM client instance
llm_client = LLMClient()
