"""
QueryMind FastAPI Backend — with chat history.

Endpoints:
  POST   /api/chats                       create a new chat
  GET    /api/chats                       list all chats
  GET    /api/chats/{chat_id}/messages    fetch messages in a chat
  POST   /api/chats/{chat_id}/messages    send a message, get AI reply
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import close_pool
from gemini_client import run_conversation
from title_generator import generate_title
from models import (
    ChatSummary,
    ChatMessage,
    UpdateChatRequest,
    SendMessageRequest,
    SendMessageResponse,
)
import chat_repository as repo


@asynccontextmanager
async def lifespan(app: FastAPI):
    # The pool is created lazily on first DB use (serverless-friendly). We do NOT
    # eagerly connect here, so an unreachable database can't crash startup — the
    # health check still responds and DB errors surface as clean per-request 500s.
    print("[Startup] Ready.")
    yield
    print("[Shutdown] Closing database pool...")
    await close_pool()
    print("[Shutdown] Done.")


app = FastAPI(
    title="QueryMind API",
    description="AI-powered natural language insights over benchmark data",
    version="0.2.0",
    lifespan=lifespan,
)

# Allowed frontend origins. Defaults to the local Vite dev server; in
# production set FRONTEND_ORIGIN to your deployed frontend URL(s),
# comma-separated, e.g. "https://query-mind-blush.vercel.app".
_origins_env = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
# Normalize: split on commas and strip any trailing slash, since CORS origins
# are matched exactly and a browser Origin header never has a trailing slash.
ALLOWED_ORIGINS = [o.strip().rstrip("/") for o in _origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "ok", "service": "querymind"}


# ─── Chats ───────────────────────────────────────────────────────────────────

@app.post("/api/chats", response_model=ChatSummary)
async def create_chat():
    """Create a new empty chat. Title starts as 'New chat'."""
    chat = await repo.create_chat()
    return ChatSummary(**chat)


@app.get("/api/chats", response_model=list[ChatSummary])
async def list_chats():
    """List all chats, most recently updated first."""
    chats = await repo.list_chats()
    return [ChatSummary(**c) for c in chats]


@app.patch("/api/chats/{chat_id}", response_model=ChatSummary)
async def update_chat(chat_id: str, request: UpdateChatRequest):
    """Rename a chat."""
    chat = await repo.get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    await repo.update_chat_title(chat_id, request.title)
    updated = await repo.get_chat(chat_id)
    return ChatSummary(**updated)


@app.delete("/api/chats/{chat_id}", status_code=204)
async def delete_chat(chat_id: str):
    """Delete a chat and all its messages."""
    deleted = await repo.delete_chat(chat_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found")
    return None


# ─── Messages ────────────────────────────────────────────────────────────────

@app.get("/api/chats/{chat_id}/messages", response_model=list[ChatMessage])
async def get_messages(chat_id: str):
    """Get all messages in a chat, oldest first."""
    chat = await repo.get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")
    messages = await repo.list_messages(chat_id)
    return [ChatMessage(**m) for m in messages]


@app.post("/api/chats/{chat_id}/messages", response_model=SendMessageResponse)
async def send_message(chat_id: str, request: SendMessageRequest):
    """
    Send a message in a chat.

    Flow:
      1. Verify the chat exists
      2. Persist the user message
      3. Fetch full history (so Gemini has context)
      4. Run the AI tool-calling loop
      5. Persist the assistant message
      6. If this was the first user message, generate a title
      7. Return both messages + (possibly updated) chat title
    """
    chat = await repo.get_chat(chat_id)
    if chat is None:
        raise HTTPException(status_code=404, detail="Chat not found")

    try:
        # 1. Persist user message
        user_msg = await repo.add_user_message(chat_id, request.message)

        # 2. Load history (now includes the message we just added)
        history = await repo.list_messages(chat_id)
        history_for_gemini = [
            {"role": m["role"], "content": m["content"]} for m in history
        ]

        # 3. Run AI loop
        ai_response = await run_conversation(history_for_gemini)

        # 4. Persist assistant message
        assistant_msg = await repo.add_assistant_message(
            chat_id=chat_id,
            content=ai_response["insight"],
            chart_type=ai_response.get("chart_type"),
            chart_data=ai_response.get("chart_data"),
        )

        # 5. Bump updated_at so the sidebar reorders
        await repo.touch_chat(chat_id)

        # 6. If this was the first user message, generate a title
        current_title = chat["title"]
        user_message_count = sum(1 for m in history if m["role"] == "user")
        if user_message_count == 1 and current_title == "New chat":
            new_title = await generate_title(request.message)
            await repo.update_chat_title(chat_id, new_title)
            current_title = new_title

        return SendMessageResponse(
            user_message=ChatMessage(**user_msg),
            assistant_message=ChatMessage(**assistant_msg),
            chat_title=current_title,
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Error] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
