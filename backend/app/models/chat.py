from pydantic import BaseModel
from datetime import datetime

class ChatSession(BaseModel):
    id: str
    title: str
    service_id: str | None
    message_count: int
    created_at: str
    updated_at: str

class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    thinking: str | None
    tool_calls: list[dict]
    timestamp: str

class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str
    gateway_url: str = ""
    gateway_api_key: str = ""
    llm_api_key: str
    llm_base_url: str | None = None
    service_id: str | None = None
    model: str = "gpt-4o"
