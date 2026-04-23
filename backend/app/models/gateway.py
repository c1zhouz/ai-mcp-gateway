from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict

class GatewayConfig(BaseModel):
    name: str
    listen_address: str
    port: int
    timeout_ms: int
    max_concurrency: int
    log_level: str
    log_retention_days: int

class ApiKeyCreate(BaseModel):
    name: str
    permissions: List[str] = ["read"]
    expires_at: Optional[str] = None

class RouteRuleCreate(BaseModel):
    path_pattern: str
    target_service_id: str
    priority: int = 0
