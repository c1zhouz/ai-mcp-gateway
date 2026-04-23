from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

class ChatSession(BaseModel):
    id: str
    title: str
    service_id: Optional[str]
    message_count: int
    created_at: str
    updated_at: str

class ChatMessage(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    thinking: Optional[str]
    tool_calls: List[Dict]
    timestamp: str

class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str
    gateway_url: str = ""
    gateway_api_key: str = ""
    llm_api_key: str
    llm_base_url: Optional[str] = None
    service_id: Optional[str] = None
    model: str = "gpt-4o"
