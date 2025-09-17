from typing import Dict, Optional, cast, Any, List
import os
import json
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import BaseTool
from langchain_ollama import OllamaLLM
from google import genai
from google.genai import types
from .prompts import AGENT_PROMPT
from .tools import web_search_tool, retriever_tool, memory_tool


class GoogleGenAIWrapper:
    """Wrapper to make Google Gen AI SDK compatible with LangChain."""

    def __init__(self, client, model_name):
        self.client = client
        self.model_name = model_name

    def _convert_tools_to_genai_format(self, tools: List[BaseTool]) -> List[types.Tool]:
        """Convert LangChain tools to Google Gen AI format."""
        genai_tools = []

        for tool in tools:
            # Create function declaration for each tool
            function_declaration = types.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=types.Schema(
                    type="OBJECT",
                    properties={
                        "input": types.Schema(
                            type="STRING", description="Input for the tool"
                        )
                    },
                    required=["input"],
                ),
            )

            genai_tool = types.Tool(function_declarations=[function_declaration])
            genai_tools.append(genai_tool)

        return genai_tools

    def invoke(self, prompt, tools=None):
        """Sync invoke method for LangChain compatibility."""
        try:
            config = types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=1000,
            )

            if tools:
                genai_tools = self._convert_tools_to_genai_format(tools)
                config.tools = genai_tools

            response = self.client.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )

            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    async def ainvoke(self, prompt, **kwargs):
        """Async invoke method for LangChain compatibility."""
        return self.invoke(prompt, **kwargs)

    def __call__(self, prompt, **kwargs):
        """Make the wrapper callable."""
        return self.invoke(prompt, **kwargs)


async def run_agent(query: str, model: str) -> Dict[str, Optional[str]]:
    """
    Runs the agent loop.
    """
    if model == "phi3":
        llm = OllamaLLM(model="phi3")
    else:
        # Check if Google API key is available
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            return {
                "answer": "Error: Google API key not found. Please set GOOGLE_API_KEY in your .env file to use Gemini models.",
                "tool_used": None,
            }

        try:
            # Create Google Gen AI client
            client = genai.Client(api_key=google_api_key)

            # Create wrapper for LangChain compatibility
            llm = GoogleGenAIWrapper(client, model)
        except Exception as e:
            error_msg = str(e)
            if "API_KEY_INVALID" in error_msg or "invalid API key" in error_msg.lower():
                return {
                    "answer": "Error: The Google API key is invalid. Please check your GOOGLE_API_KEY in the .env file and ensure it's a valid key from Google AI Studio.",
                    "tool_used": None,
                }
            return {
                "answer": f"Error initializing Gemini model: {error_msg}",
                "tool_used": None,
            }

    # Type cast the tools to satisfy type checker
    tools = cast(list[BaseTool], [web_search_tool, retriever_tool, memory_tool])

    agent = create_react_agent(llm, tools, AGENT_PROMPT)  # type: ignore
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True,
        return_intermediate_steps=True,
    )

    try:
        response = await agent_executor.ainvoke({"input": query})
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg or "API key not valid" in error_msg:
            return {
                "answer": "Error: The Google API key is invalid or expired. Please update your GOOGLE_API_KEY in the .env file with a valid key from Google AI Studio.",
                "tool_used": None,
            }
        return {
            "answer": f"Error during agent execution: {error_msg}",
            "tool_used": None,
        }

    tool_used = None
    if "intermediate_steps" in response and response["intermediate_steps"]:
        tool_used = response["intermediate_steps"][0][0].tool

    return {"answer": response.get("output"), "tool_used": tool_used}
