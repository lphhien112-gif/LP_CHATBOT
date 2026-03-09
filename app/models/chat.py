# /app/models/chat.py
from pydantic import BaseModel
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    user_id: Optional[str] = "default_user"

class ChatResponse(BaseModel):
    text_response: str
    allow_html: Optional[bool] = False
    suggestions: Optional[list] = []
    logs: Optional[list] = []
