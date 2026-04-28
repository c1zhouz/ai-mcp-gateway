from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict


class ServiceCreate(BaseModel):
    name: str
    address: str
    description: str = ""
    health_check_interval: int = 30
    auto_reconnect: bool = True
    source_file: str = ""
    python_path: str = ""


class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None
    health_check_interval: Optional[int] = None
    auto_reconnect: Optional[bool] = None
    source_file: Optional[str] = None
    python_path: Optional[str] = None


class ServiceResponse(BaseModel):
    id: str
    name: str
    address: str
    description: str
    status: str
    health_check_interval: int
    auto_reconnect: bool
    tool_count: int
    last_heartbeat: Optional[str]
    created_at: str
