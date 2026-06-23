import logging

from fastapi import FastAPI, HTTPException

from app.config import get_settings
from app.schemas import HealthResponse, MessageRequest, MessageResponse
from app.service import process_message

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(title="Tito Marlon AI Family Assistant")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/message", response_model=MessageResponse)
def message(payload: MessageRequest) -> MessageResponse:
    try:
        return process_message(payload)
    except Exception:
        logger.exception("Failed to process message")
        if settings.app_env == "development":
            raise
        raise HTTPException(status_code=500, detail="Internal server error")
