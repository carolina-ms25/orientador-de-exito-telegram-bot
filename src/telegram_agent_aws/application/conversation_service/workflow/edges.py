from typing import Literal

from langgraph.graph import END

from telegram_agent_aws.application.conversation_service.workflow.state import TelegramAgentState


def should_use_rag(state: TelegramAgentState) -> Literal["tools", "generate_final_response_node"]:
    """
    Determine if RAG should be used based on detected intention.
    Force RAG for academic information queries.
    """
    intention = state.get("intention", "general")
    
    if intention == "academic_info":
        # Force RAG for academic questions
        return "tools"
    else:
        # Skip RAG for greetings, contact data, and general conversation
        return "generate_final_response_node"


def should_summarize_conversation(state: TelegramAgentState) -> Literal["summarize_conversation_node", END]:
    messages = state["messages"]

    if len(messages) > 30:
        return "summarize_conversation_node"

    return END
