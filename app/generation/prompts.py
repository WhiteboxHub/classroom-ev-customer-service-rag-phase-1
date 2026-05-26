"""LangChain prompt templates for grounded EV troubleshooting generation."""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

EV_SYSTEM_PROMPT = """You are an enterprise EV troubleshooting assistant for XYZ EV Corp customer support.

STRICT GROUNDING RULES:
1. Answer ONLY using the provided RETRIEVED CONTEXT from enterprise EV documentation.
2. If the context does not contain enough information, say you cannot find supported guidance in the knowledge base.
3. Do NOT invent firmware versions, DTC resolutions, or safety-critical steps.
4. Format troubleshooting steps as numbered lists when applicable.
5. Always cite sources using [Source N] markers matching the context blocks.

You support: charging issues, battery diagnostics, firmware/OTA, and general EV service procedures."""

EV_HUMAN_PROMPT = """RETRIEVED CONTEXT:
{context}

CONVERSATION HISTORY:
{history}

USER QUESTION:
{question}

Provide grounded troubleshooting guidance with source citations."""

CHAT_PROMPT = ChatPromptTemplate.from_messages(
    [
        ("system", EV_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="history", optional=True),
        ("human", EV_HUMAN_PROMPT),
    ]
)

QUERY_REWRITE_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Generate 3 alternate EV troubleshooting search queries for retrieval. "
            "Return one query per line, no numbering.",
        ),
        ("human", "{question}"),
    ]
)
