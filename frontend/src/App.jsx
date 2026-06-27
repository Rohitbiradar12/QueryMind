import { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import InsightPanel from './components/InsightPanel'
import { createChat, listChats, getMessages, sendMessage, deleteChat, renameChat } from './api/chat'

export default function App() {
  // ── Sidebar state ────────────────────────────────────────────────────────
  const [chats, setChats] = useState([])

  // ── Active chat state ────────────────────────────────────────────────────
  const [activeChatId, setActiveChatId] = useState(null)
  const [messages, setMessages] = useState([])

  // ── Latest response (drives the right panel) ─────────────────────────────
  const [latestResponse, setLatestResponse] = useState(null)

  // ── Loading ──────────────────────────────────────────────────────────────
  const [isLoading, setIsLoading] = useState(false)

  // ── Typewriter animation tracking ─────────────────────────────────────────
  // Only freshly-arrived messages animate; history loads instantly.
  const [animatingMessageIds, setAnimatingMessageIds] = useState(new Set())
  const [animateInsight, setAnimateInsight] = useState(false)

  // ── Load chats on mount ──────────────────────────────────────────────────
  const refreshChats = useCallback(async () => {
    try {
      const list = await listChats()
      setChats(list)
    } catch (err) {
      console.error('Failed to list chats:', err)
    }
  }, [])

  useEffect(() => {
    refreshChats()
  }, [refreshChats])

  // ── Load messages when switching chats ───────────────────────────────────
  useEffect(() => {
    // Switching chats must never animate old history.
    setAnimatingMessageIds(new Set())
    setAnimateInsight(false)

    if (!activeChatId) {
      setMessages([])
      setLatestResponse(null)
      return
    }
    ;(async () => {
      try {
        const msgs = await getMessages(activeChatId)
        setMessages(msgs)

        // Find the latest assistant message — that drives the right panel
        const lastAssistant = [...msgs].reverse().find((m) => m.role === 'assistant')
        if (lastAssistant) {
          setLatestResponse({
            insight: lastAssistant.content,
            chart_type: lastAssistant.chart_type,
            chart_data: lastAssistant.chart_data,
          })
        } else {
          setLatestResponse(null)
        }
      } catch (err) {
        console.error('Failed to load messages:', err)
        setMessages([])
        setLatestResponse(null)
      }
    })()
  }, [activeChatId])

  // ── New chat ─────────────────────────────────────────────────────────────
  const handleNewChat = async () => {
    try {
      const chat = await createChat()
      setActiveChatId(chat.chat_id)
      await refreshChats()
    } catch (err) {
      console.error('Failed to create chat:', err)
    }
  }

  // ── Select existing chat ─────────────────────────────────────────────────
  const handleSelectChat = (chatId) => {
    setActiveChatId(chatId)
  }

  // ── Rename chat ──────────────────────────────────────────────────────────
  const handleRenameChat = async (chatId, title) => {
    // Optimistic: update the sidebar title immediately
    setChats((prev) =>
      prev.map((c) => (c.chat_id === chatId ? { ...c, title } : c))
    )
    try {
      await renameChat(chatId, title)
      await refreshChats()
    } catch (err) {
      console.error('Failed to rename chat:', err)
      await refreshChats() // revert to server truth on failure
    }
  }

  // ── Delete chat ──────────────────────────────────────────────────────────
  const handleDeleteChat = async (chatId) => {
    if (!window.confirm('Delete this chat? This cannot be undone.')) return
    try {
      await deleteChat(chatId)
      // If we deleted the chat we were viewing, clear the main panel
      if (chatId === activeChatId) {
        setActiveChatId(null)
        setMessages([])
        setLatestResponse(null)
      }
      await refreshChats()
    } catch (err) {
      console.error('Failed to delete chat:', err)
    }
  }

  // ── Send message ─────────────────────────────────────────────────────────
  const handleSend = async (text) => {
    // If no chat is active, create one first
    let chatId = activeChatId
    if (!chatId) {
      try {
        const chat = await createChat()
        chatId = chat.chat_id
        setActiveChatId(chatId)
      } catch (err) {
        console.error('Failed to create chat:', err)
        return
      }
    }

    // Optimistic: add the user message to the UI immediately
    const optimisticUserMsg = {
      message_id: `temp-${Date.now()}`,
      role: 'user',
      content: text,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, optimisticUserMsg])
    setIsLoading(true)

    try {
      const response = await sendMessage(chatId, text)

      // Replace optimistic message with the real one + append assistant message
      setMessages((prev) => {
        const withoutOptimistic = prev.filter((m) => m.message_id !== optimisticUserMsg.message_id)
        return [...withoutOptimistic, response.user_message, response.assistant_message]
      })

      // Drive the right panel
      setLatestResponse({
        insight: response.assistant_message.content,
        chart_type: response.assistant_message.chart_type,
        chart_data: response.assistant_message.chart_data,
      })

      // Mark this assistant message + insight as freshly arrived → animate
      setAnimatingMessageIds((prev) => {
        const next = new Set(prev)
        next.add(response.assistant_message.message_id)
        return next
      })
      setAnimateInsight(true)

      // Refresh sidebar — title may have changed, updated_at definitely did
      await refreshChats()
    } catch (err) {
      console.error('Send failed:', err)
      // Mark the optimistic message with an error
      setMessages((prev) => [
        ...prev,
        {
          message_id: `error-${Date.now()}`,
          role: 'assistant',
          content: `Error: ${err.message}`,
          created_at: new Date().toISOString(),
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="h-full flex bg-[#0a0a0a] text-white font-sans">
      {/* Sidebar */}
      <div className="w-64 flex-shrink-0">
        <Sidebar
          chats={chats}
          activeChatId={activeChatId}
          onSelectChat={handleSelectChat}
          onNewChat={handleNewChat}
          onDeleteChat={handleDeleteChat}
          onRenameChat={handleRenameChat}
          isLoading={isLoading}
        />
      </div>

      {/* Chat panel */}
      <div className="flex-1 min-w-0 border-r border-white/[0.06]">
        <ChatPanel
          messages={messages}
          onSend={handleSend}
          isLoading={isLoading}
          hasActiveChat={!!activeChatId}
          animatingMessageIds={animatingMessageIds}
        />
      </div>

      {/* Insight panel */}
      <div className="w-[440px] flex-shrink-0">
        <InsightPanel latestResponse={latestResponse} isLoading={isLoading} animateInsight={animateInsight} />
      </div>
    </div>
  )
}
