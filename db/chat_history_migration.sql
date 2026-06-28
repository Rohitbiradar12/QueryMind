-- ============================================================
-- QueryMind — Phase 6A: Chat History Migration
-- ============================================================
-- Adds two tables for persistent, multi-turn chat history.
-- Run in pgAdmin Query Tool against the `querymind` database.
--
-- Safe to run once. If gen_random_uuid() is unavailable
-- (Postgres < 13), uncomment the pgcrypto line below first.
-- ============================================================

-- CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Chats: one row per conversation
CREATE TABLE chats (
    chat_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title        VARCHAR(200) NOT NULL DEFAULT 'New chat',
    created_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Messages: every user and assistant turn, in order
CREATE TABLE chat_messages (
    message_id   SERIAL PRIMARY KEY,
    chat_id      UUID NOT NULL REFERENCES chats(chat_id) ON DELETE CASCADE,
    role         VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content      TEXT NOT NULL,
    chart_type   VARCHAR(20),             -- nullable; only set on assistant messages
    chart_data   JSONB,                    -- nullable; chart payload for assistant messages
    created_at   TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Index for fast lookup by chat
CREATE INDEX idx_chat_messages_chat_id ON chat_messages(chat_id, created_at);

-- Index for sorting chats by recency in the sidebar
CREATE INDEX idx_chats_updated_at ON chats(updated_at DESC);
