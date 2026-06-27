const BASE = 'http://localhost:8000'

async function handle(response) {
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`${response.status}: ${text}`)
  }
  return response.json()
}

/** POST /api/chats — returns the new chat */
export async function createChat() {
  return handle(await fetch(`${BASE}/api/chats`, { method: 'POST' }))
}

/** GET /api/chats — returns all chats, newest first */
export async function listChats() {
  return handle(await fetch(`${BASE}/api/chats`))
}

/** PATCH /api/chats/{chat_id} — rename a chat */
export async function renameChat(chatId, title) {
  return handle(
    await fetch(`${BASE}/api/chats/${chatId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
  )
}

/** DELETE /api/chats/{chat_id} — removes a chat and its messages */
export async function deleteChat(chatId) {
  const response = await fetch(`${BASE}/api/chats/${chatId}`, { method: 'DELETE' })
  if (!response.ok) {
    const text = await response.text()
    throw new Error(`${response.status}: ${text}`)
  }
  // 204 No Content — nothing to parse
  return true
}

/** GET /api/chats/{chat_id}/messages — returns ordered messages */
export async function getMessages(chatId) {
  return handle(await fetch(`${BASE}/api/chats/${chatId}/messages`))
}

/**
 * POST /api/chats/{chat_id}/messages — send a message, get AI reply.
 * Response: { user_message, assistant_message, chat_title }
 */
export async function sendMessage(chatId, message) {
  return handle(
    await fetch(`${BASE}/api/chats/${chatId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    })
  )
}
