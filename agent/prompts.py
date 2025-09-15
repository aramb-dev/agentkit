SYSTEM_PROMPT = """You are a helpful assistant. Your goal is to provide a concise and accurate answer to the user's query.
You have access to a set of tools to help you. Based on the user's query, you can decide to use a tool or answer directly.
If you use a tool, you will be given the tool's output. You should then use this output to construct your final answer.
"""

SUMMARY_PROMPT = """Given the user's query and the output from a tool, provide a concise and accurate answer.
User query: {query}
Tool output: {tool_output}
"""
