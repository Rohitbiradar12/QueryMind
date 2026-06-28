"""
chat_repository.py — CRUD operations for chats and chat_messages.

Same pattern as tools.py: async functions returning plain dicts.
Difference: this layer DOES write to the DB (create chat, append message),
unlike the read-only analysis tools.
"""

from datetime import datetime
from uuid import UUID
import json

from database import get_pool


def _row_to_dict(row) -> dict:
    """Convert asyncpg Record → dict, handle datetimes and UUIDs."""
    if row is None:
        return None
    d = dict(row)
    for key, value in d.items():
        if isinstance(value, datetime):
            d[key] = value.isoformat()
        elif isinstance(value, UUID):
            d[key] = str(value)
    # asyncpg returns JSONB as a raw JSON string here (no codec registered),
    # but our Pydantic models expect a parsed list. Decode it back.
    if isinstance(d.get("chart_data"), str):
        try:
            d["chart_data"] = json.loads(d["chart_data"])
        except (ValueError, TypeError):
            pass
    return d


# ─── Chats ───────────────────────────────────────────────────────────────────

async def create_chat() -> dict:
    """Create a new chat with default title. Returns the new row."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO chats DEFAULT VALUES
            RETURNING chat_id, title, created_at, updated_at
        """)
        return _row_to_dict(row)


async def list_chats() -> list[dict]:
    """Returns all chats ordered by most-recently-updated first."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT chat_id, title, created_at, updated_at
            FROM chats
            ORDER BY updated_at DESC
        """)
        return [_row_to_dict(r) for r in rows]


async def get_chat(chat_id: str) -> dict | None:
    """Returns a single chat by ID, or None if missing."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT chat_id, title, created_at, updated_at
            FROM chats
            WHERE chat_id = $1
        """, UUID(chat_id))
        return _row_to_dict(row)


async def update_chat_title(chat_id: str, title: str) -> None:
    """Set a chat's title."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE chats SET title = $1, updated_at = NOW()
            WHERE chat_id = $2
        """, title, UUID(chat_id))


async def delete_chat(chat_id: str) -> bool:
    """Delete a chat and (via ON DELETE CASCADE) its messages.

    Returns True if a row was deleted, False if the chat didn't exist.
    """
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute("""
            DELETE FROM chats WHERE chat_id = $1
        """, UUID(chat_id))
        # asyncpg returns a status string like "DELETE 1"
        return result.endswith("1")


async def touch_chat(chat_id: str) -> None:
    """Bump updated_at to NOW() — called after adding a message."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            UPDATE chats SET updated_at = NOW() WHERE chat_id = $1
        """, UUID(chat_id))


# ─── Messages ────────────────────────────────────────────────────────────────

async def list_messages(chat_id: str) -> list[dict]:
    """Returns all messages in a chat, oldest first."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT message_id, role, content, chart_type, chart_data, created_at
            FROM chat_messages
            WHERE chat_id = $1
            ORDER BY created_at ASC, message_id ASC
        """, UUID(chat_id))

        result = []
        for r in rows:
            d = _row_to_dict(r)
            # asyncpg returns JSONB as a Python object already; no extra parse needed
            result.append(d)
        return result


async def add_user_message(chat_id: str, content: str) -> dict:
    """Insert a user message. Returns the new row."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            INSERT INTO chat_messages (chat_id, role, content)
            VALUES ($1, 'user', $2)
            RETURNING message_id, role, content, chart_type, chart_data, created_at
        """, UUID(chat_id), content)
        return _row_to_dict(row)


async def add_assistant_message(
    chat_id: str,
    content: str,
    chart_type: str | None,
    chart_data: list | None,
) -> dict:
    """Insert an assistant message with optional chart payload."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        chart_data_json = json.dumps(chart_data) if chart_data is not None else None
        row = await conn.fetchrow("""
            INSERT INTO chat_messages (chat_id, role, content, chart_type, chart_data)
            VALUES ($1, 'assistant', $2, $3, $4::jsonb)
            RETURNING message_id, role, content, chart_type, chart_data, created_at
        """, UUID(chat_id), content, chart_type, chart_data_json)
        return _row_to_dict(row)
