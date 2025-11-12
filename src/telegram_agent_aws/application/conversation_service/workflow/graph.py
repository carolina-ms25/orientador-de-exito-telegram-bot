from functools import lru_cache

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from telegram_agent_aws.application.conversation_service.workflow.edges import should_summarize_conversation, should_use_rag
from telegram_agent_aws.application.conversation_service.workflow.nodes import (
    generate_final_response_node,
    generate_rag_response_node,
    generate_text_response_node,
    intention_detection_node,
    router_node,
    summarize_conversation_node,
)
from telegram_agent_aws.application.conversation_service.workflow.state import TelegramAgentState
from telegram_agent_aws.application.conversation_service.workflow.tools import get_retriever_tool

retriever_tool = get_retriever_tool()


@lru_cache(maxsize=1)
def create_workflow_graph():
    graph_builder = StateGraph(TelegramAgentState)

    # Add all nodes
    graph_builder.add_node("intention_detection_node", intention_detection_node)
    graph_builder.add_node("router_node", router_node)
    graph_builder.add_node("generate_text_response_node", generate_text_response_node)
    graph_builder.add_node("generate_rag_response_node", generate_rag_response_node)
    graph_builder.add_node("summarize_conversation_node", summarize_conversation_node)
    graph_builder.add_node("tools", ToolNode([retriever_tool]))
    graph_builder.add_node("generate_final_response_node", generate_final_response_node)

    # Define workflow edges
    graph_builder.add_edge(START, "intention_detection_node")
    graph_builder.add_edge("intention_detection_node", "router_node")
    graph_builder.add_edge("router_node", "generate_text_response_node")
    
    # Smart RAG routing based on intention
    graph_builder.add_conditional_edges(
        "generate_text_response_node", 
        should_use_rag, 
        {
            "tools": "tools", 
            "generate_final_response_node": "generate_final_response_node"
        }
    )
    
    # After tools, generate final response with retrieved context
    graph_builder.add_edge("tools", "generate_rag_response_node")
    graph_builder.add_edge("generate_rag_response_node", "generate_final_response_node")
    
    # Check if conversation needs summarization
    graph_builder.add_conditional_edges("generate_final_response_node", should_summarize_conversation)
    graph_builder.add_edge("summarize_conversation_node", END)

    return graph_builder
