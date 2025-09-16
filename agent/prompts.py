from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

AGENT_PROMPT = ChatPromptTemplate.from_messages(  # type: ignore
    [
        ("system", "You are a helpful assistant."),
        ("user", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ]
)
