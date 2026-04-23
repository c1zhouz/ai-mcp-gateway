from pydantic import BaseModel

class ToolResponse(BaseModel):
    id: str
    service_id: str
    name: str
    description: str
    parameters_schema: dict
    enabled: bool
    call_count: int
