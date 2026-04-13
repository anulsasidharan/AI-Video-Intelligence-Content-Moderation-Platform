import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.agent_audit import AgentAuditStatus


class AgentAuditLogResponse(BaseModel):
    id: uuid.UUID
    agent_id: str
    action_type: str
    description: str
    input_ref: str
    output_summary: str | None
    status: AgentAuditStatus
    execution_time_ms: int | None
    triggered_by: str
    trace_id: str
    correlation_id: str | None
    event_timestamp: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentAuditListResponse(BaseModel):
    items: list[AgentAuditLogResponse]
    total: int


class AgentAuditCreate(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    action_type: str = Field(..., min_length=1, max_length=64)
    description: str = Field(..., min_length=1, max_length=512)
    input_ref: str = Field(..., min_length=1, max_length=255)
    output_summary: str | None = Field(default=None, max_length=512)
    status: AgentAuditStatus
    execution_time_ms: int | None = Field(default=None, ge=0)
    triggered_by: str = Field(..., min_length=1, max_length=32)
    trace_id: str = Field(..., min_length=1, max_length=64)
    correlation_id: str | None = Field(default=None, max_length=64)
    event_timestamp: datetime | None = None

    model_config = ConfigDict(str_strip_whitespace=True)
