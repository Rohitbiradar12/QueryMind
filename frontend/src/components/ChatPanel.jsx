import { useState, useRef, useEffect } from 'react'
import Message from './Message'
import EmptyState from './EmptyState'

export default function ChatPanel({ messages, onSend, isLoading, hasActiveChat, animatingMessageIds }) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSubmit = () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading || !hasActiveChat) return
    onSend(trimmed)
    setInput('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="h-full flex flex-col bg-[#0a0a0a]">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        {!hasActiveChat ? (
          <EmptyState onSuggestion={onSend} disabled={isLoading} />
        ) : messages.length === 0 && !isLoading ? (
          <EmptyState onSuggestion={onSend} disabled={isLoading} />
        ) : (
          <div className="max-w-3xl mx-auto px-6 py-8 space-y-6">
            {messages.map((msg) => (
              <Message
                key={msg.message_id}
                role={msg.role}
                content={msg.content}
                animate={animatingMessageIds?.has(msg.message_id) ?? false}
              />
            ))}

            {isLoading && (
              <div className="flex justify-start animate-fade-in">
                <div className="text-sm text-white/40">
                  <div className="text-[10px] uppercase tracking-wider font-mono mb-1.5">
                    Assistant
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="w-1.5 h-1.5 rounded-full bg-white/30 animate-pulse" />
                    <div className="w-1.5 h-1.5 rounded-full bg-white/30 animate-pulse" style={{ animationDelay: '150ms' }} />
                    <div className="w-1.5 h-1.5 rounded-full bg-white/30 animate-pulse" style={{ animationDelay: '300ms' }} />
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-white/[0.06] px-6 py-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex gap-2 items-end">
            <div className="flex-1 relative">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading || !hasActiveChat}
                placeholder={
                  hasActiveChat
                    ? 'Ask a follow-up...'
                    : 'Select a chat or start a new one'
                }
                className="w-full bg-white/[0.04] border border-white/[0.06] focus:border-white/[0.2] rounded-md px-4 py-3 text-sm text-white placeholder-white/30 transition-colors disabled:opacity-50"
              />
            </div>
            <button
              onClick={handleSubmit}
              disabled={isLoading || !input.trim() || !hasActiveChat}
              title="Send message"
              aria-label="Send message"
              className="flex-shrink-0 flex items-center justify-center w-11 h-11 rounded-md bg-accent hover:bg-accent-hover text-white transition-colors disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:bg-accent"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <line x1="12" y1="19" x2="12" y2="5" />
                <polyline points="5 12 12 5 19 12" />
              </svg>
            </button>
          </div>
          <div className="text-[10px] text-white/30 font-mono mt-2 text-center">
            Enter to send · Shift+Enter for new line
          </div>
        </div>
      </div>
    </div>
  )
}
