from pydantic import BaseModel
from datetime import datetime


class ServiceCreate(BaseModel):
    name: str
    address: str
    description: str = ""
    health_check_interval: int = 30
    auto_reconnect: bool = True


class ServiceUpdate(BaseModel):
    name: str | None = None
    address: str | None = None
    description: str | None = None
    health_check_interval: int | None = None
    auto_reconnect: bool | None = None


class ServiceResponse(BaseModel):
    id: str
    name: str
    address: str
    description: str
    status: str
    health_check_interval: int
    auto_reconnect: bool
    tool_count: int
    last_heartbeat: str | None
    created_at: str
