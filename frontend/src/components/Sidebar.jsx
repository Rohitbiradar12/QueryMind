import { useState, useRef, useEffect } from 'react'
import { relativeTime } from '../lib/format'

export default function Sidebar({
  chats,
  activeChatId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onRenameChat,
  isLoading,
}) {
  // Which chat's "..." menu is currently open
  const [menuOpenId, setMenuOpenId] = useState(null)
  // Which chat is being renamed inline, and the draft text
  const [editingId, setEditingId] = useState(null)
  const [draftTitle, setDraftTitle] = useState('')
  const inputRef = useRef(null)

  useEffect(() => {
    if (editingId && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [editingId])

  const startRename = (chat) => {
    setMenuOpenId(null)
    setEditingId(chat.chat_id)
    setDraftTitle(chat.title)
  }

  const commitRename = (chatId) => {
    const trimmed = draftTitle.trim()
    const original = chats.find((c) => c.chat_id === chatId)?.title
    setEditingId(null)
    if (trimmed && trimmed !== original) {
      onRenameChat(chatId, trimmed)
    }
  }

  const handleEditKeyDown = (e, chatId) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      commitRename(chatId)
    } else if (e.key === 'Escape') {
      e.preventDefault()
      setEditingId(null)
    }
  }

  return (
    <div className="h-full flex flex-col bg-[#0a0a0a] border-r border-white/[0.06]">
      {/* Header */}
      <div className="px-4 py-4 border-b border-white/[0.06]">
        <div className="flex items-center justify-between mb-3">
          <div className="font-medium tracking-tight">QueryMind</div>
          <div className="text-[10px] font-mono text-white/40 uppercase tracking-wider">v0.2</div>
        </div>
        <button
          onClick={onNewChat}
          disabled={isLoading}
          className="w-full px-3 py-2 text-sm rounded-md bg-white/[0.04] hover:bg-white/[0.08] border border-white/[0.06] transition-colors text-white/90 font-medium disabled:opacity-50"
        >
          + New chat
        </button>
      </div>

      {/* Chat list */}
      <div className="flex-1 overflow-y-auto py-2">
        {chats.length === 0 && (
          <div className="px-4 py-8 text-center text-xs text-white/30">
            No chats yet
          </div>
        )}

        {chats.map((chat) => {
          const isActive = chat.chat_id === activeChatId
          const isEditing = chat.chat_id === editingId
          const isMenuOpen = chat.chat_id === menuOpenId
          return (
            <div
              key={chat.chat_id}
              className={`group relative flex items-center transition-colors border-l-2 ${
                isActive
                  ? 'bg-white/[0.04] border-l-accent'
                  : 'border-l-transparent hover:bg-white/[0.02]'
              }`}
            >
              {isEditing ? (
                <input
                  ref={inputRef}
                  value={draftTitle}
                  onChange={(e) => setDraftTitle(e.target.value)}
                  onKeyDown={(e) => handleEditKeyDown(e, chat.chat_id)}
                  onBlur={() => commitRename(chat.chat_id)}
                  maxLength={200}
                  className="flex-1 min-w-0 mx-3 my-2 bg-white/[0.06] border border-white/[0.2] rounded px-2 py-1.5 text-sm text-white"
                />
              ) : (
                <button
                  onClick={() => onSelectChat(chat.chat_id)}
                  className="flex-1 min-w-0 text-left pl-4 pr-9 py-3"
                >
                  <div className={`text-sm truncate ${isActive ? 'text-white' : 'text-white/80'}`}>
                    {chat.title}
                  </div>
                  <div className="text-[11px] text-white/40 mt-0.5 font-mono">
                    {relativeTime(chat.updated_at)}
                  </div>
                </button>
              )}

              {/* Three-dots options button */}
              {!isEditing && (
                <button
                  onClick={() => setMenuOpenId(isMenuOpen ? null : chat.chat_id)}
                  disabled={isLoading}
                  title="Options"
                  aria-label="Chat options"
                  className={`absolute right-2 top-1/2 -translate-y-1/2 w-6 h-6 flex items-center justify-center rounded-md text-white/40 transition-all hover:bg-white/[0.08] hover:text-white/90 ${
                    isMenuOpen ? 'opacity-100 bg-white/[0.08] text-white/90' : 'opacity-0 group-hover:opacity-100'
                  }`}
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="12" cy="5" r="1.6" />
                    <circle cx="12" cy="12" r="1.6" />
                    <circle cx="12" cy="19" r="1.6" />
                  </svg>
                </button>
              )}

              {/* Dropdown menu */}
              {isMenuOpen && (
                <>
                  {/* Click-away backdrop */}
                  <div
                    className="fixed inset-0 z-10"
                    onClick={() => setMenuOpenId(null)}
                  />
                  <div className="absolute right-2 top-[calc(50%+14px)] z-20 w-36 py-1 rounded-md bg-[#141414] border border-white/[0.1] shadow-lg shadow-black/40 animate-fade-in">
                    <button
                      onClick={() => startRename(chat)}
                      className="w-full text-left px-3 py-2 text-sm text-white/80 hover:bg-white/[0.06] hover:text-white transition-colors"
                    >
                      Rename
                    </button>
                    <button
                      onClick={() => {
                        setMenuOpenId(null)
                        onDeleteChat(chat.chat_id)
                      }}
                      className="w-full text-left px-3 py-2 text-sm text-red-400/90 hover:bg-red-500/10 hover:text-red-400 transition-colors"
                    >
                      Delete chat
                    </button>
                  </div>
                </>
              )}
            </div>
          )
        })}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-white/[0.06] text-[11px] text-white/30 font-mono">
        Connected to localhost:8000
      </div>
    </div>
  )
}
