from langgraph.graph import MessagesState


class TelegramAgentState(MessagesState):
    summary: str
    response_type: str
    audio_buffer: bytes
    input_type: str  # "text" or "voice"
    intention: str   # "academic_info", "contact_data", "greeting", "general"
