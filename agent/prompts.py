from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

AGENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant. Be concise."),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
