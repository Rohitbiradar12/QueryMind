"""
Pydantic models for the QueryMind HTTP API.
"""

from typing import Literal, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ─── Chat metadata ───────────────────────────────────────────────────────────

class ChatSummary(BaseModel):
    chat_id: str
    title: str
    created_at: str
    updated_at: str


# ─── Messages ────────────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    message_id: int
    role: Literal["user", "assistant"]
    content: str
    chart_type: Optional[Literal["bar", "line", "none"]] = None
    chart_data: Optional[list[dict[str, Any]]] = None
    created_at: str


class UpdateChatRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class SendMessageRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)


class SendMessageResponse(BaseModel):
    user_message: ChatMessage
    assistant_message: ChatMessage
    chat_title: str  # may have been auto-generated on the first message
