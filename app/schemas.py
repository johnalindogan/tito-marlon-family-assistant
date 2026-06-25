from pydantic import BaseModel, Field, field_validator

from app.config import get_settings


class MessageRequest(BaseModel):
    sender_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)

    @field_validator("sender_id", "message")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("message")
    @classmethod
    def limit_message_length(cls, value: str) -> str:
        max_length = get_settings().message_max_length
        if len(value) > max_length:
            raise ValueError(f"must be {max_length} characters or fewer")
        return value


class MemorySaved(BaseModel):
    memory_key: str
    memory_value: str


class MessageResponse(BaseModel):
    reply: str
    memories_saved: list[MemorySaved] = []


class HealthResponse(BaseModel):
    status: str
