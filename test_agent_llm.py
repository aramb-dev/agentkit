#!/usr/bin/env python3

import asyncio
import os
from agent.agent import run_agent


async def test_agent():
    print("Testing AgentKit with LLM integration...")
    print("=" * 50)

    # Check if API key is available
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("⚠️  Warning: GOOGLE_API_KEY not found in environment")
        print("   The agent will use fallback responses instead of Gemini API")
        print("   To use Gemini, set your API key: export GOOGLE_API_KEY=your_key_here")
        print()

    # Test greeting
    print("=== Testing Greeting ===")
    result = await run_agent("hey!!", "gemini")
    print(f"Answer: {result['answer']}")
    print(f"Tool used: {result['tool_used']}")
    print()

    # Test search
    print("=== Testing Search ===")
    result = await run_agent("search for AI news", "gemini")
    print(f"Answer: {result['answer']}")
    print(f"Tool used: {result['tool_used']}")
    print()

    # Test architecture question
    print("=== Testing Architecture ===")
    result = await run_agent("explain the architecture", "gemini")
    print(f"Answer: {result['answer']}")
    print(f"Tool used: {result['tool_used']}")
    print()

    # Test memory
    print("=== Testing Memory ===")
    result = await run_agent("remember that I like pizza", "gemini")
    print(f"Answer: {result['answer']}")
    print(f"Tool used: {result['tool_used']}")
    print()

    # Test general question
    print("=== Testing General Question ===")
    result = await run_agent("What can you help me with?", "gemini")
    print(f"Answer: {result['answer']}")
    print(f"Tool used: {result['tool_used']}")


if __name__ == "__main__":
    asyncio.run(test_agent())
