from pydantic import BaseModel, Field, field_validator, model_validator

from app.config import get_settings


class MessageRequest(BaseModel):
    sender_id: str = Field(..., min_length=1)
    message: str = ""
    image_urls: list[str] = Field(default_factory=list, max_length=3)

    @field_validator("sender_id")
    @classmethod
    def strip_sender_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        return value.strip()

    @field_validator("message")
    @classmethod
    def limit_message_length(cls, value: str) -> str:
        max_length = get_settings().message_max_length
        if len(value) > max_length:
            raise ValueError(f"must be {max_length} characters or fewer")
        return value

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for url in value:
            url = url.strip()
            if not url:
                continue
            if not url.startswith(("http://", "https://")):
                raise ValueError("image_urls must be http or https URLs")
            cleaned.append(url)
        return cleaned[:3]

    @model_validator(mode="after")
    def require_text_or_image(self) -> "MessageRequest":
        if not self.message and not self.image_urls:
            raise ValueError("message or image_urls is required")
        return self


class MemorySaved(BaseModel):
    memory_key: str
    memory_value: str


class FamilyMemberProfile(BaseModel):
    member_key: str
    full_name: str
    preferred_name: str
    relationship_label: str
    aliases: list[str] = []
    facebook_url: str


class MessageResponse(BaseModel):
    reply: str
    memories_saved: list[MemorySaved] = []
    outbound_image_urls: list[str] = []
    identified_family_member: FamilyMemberProfile | None = None


class HealthResponse(BaseModel):
    status: str
