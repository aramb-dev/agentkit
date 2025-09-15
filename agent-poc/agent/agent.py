from .router import route_query
from .tools import web_search_tool, retriever_tool, memory_tool
from .prompts import SYSTEM_PROMPT, SUMMARY_PROMPT
from langchain.prompts import PromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.llms.fake import FakeListLLM

# A map of tool names to their corresponding functions
TOOL_MAP = {
    "web_search_tool": web_search_tool,
    "retriever_tool": retriever_tool,
    "memory_tool": memory_tool,
}

def run_agent(query: str) -> dict:
    """
    Runs the agent loop.
    """
    # For this PoC, we'll use a fake LLM
    llm = FakeListLLM(responses=["This is a direct answer from the LLM."])

    # 1. Route the query
    tool_name = route_query(query)

    if tool_name:
        # 2. If a tool is chosen, run it
        tool_function = TOOL_MAP[tool_name]
        
        # For the memory tool, we need to determine the action
        if tool_name == "memory_tool":
            if "write" in query.lower() or "remember" in query.lower():
                action = "write"
                # A simple way to extract data to write
                data_to_write = query.split(action)[-1].strip()
                tool_output = tool_function.run({"action": action, "data": data_to_write})
            else:
                action = "read"
                tool_output = tool_function.run({"action": action})
        else:
            tool_output = tool_function.run(query)

        # 3. Summarize the tool output
        summary_prompt_template = PromptTemplate.from_template(SUMMARY_PROMPT)
        summary_chain = {"query": RunnablePassthrough(), "tool_output": RunnablePassthrough()} | summary_prompt_template | llm
        
        # We pass the tool output as a string to the summary chain
        final_answer = summary_chain.invoke(tool_output)
        
        return {"answer": final_answer, "tool_used": tool_name}
    else:
        # 4. If no tool is chosen, answer directly
        final_answer = llm.invoke(query)
        return {"answer": final_answer, "tool_used": None}
