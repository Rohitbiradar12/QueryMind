# Phase 6B — Premium UI (Vercel / Lovable Aesthetic)

## Goal of This Phase

Redesign the frontend to look like a production tool, not a POC. By the end of this phase:

- **3-panel layout**: chat sidebar | conversation | insight + chart
- **Geist font** (Vercel's signature typeface) for both sans and mono
- **Hairline borders, deep blacks, subtle accents** — the Vercel/Lovable look
- **New chat button + clickable chat history** in the sidebar
- **Auto-generated titles** show up in the sidebar after the first message
- **Smooth transitions** on every interactive element
- **Loading states** that feel intentional, not janky

The backend stays exactly as Phase 6A left it. We're only touching the frontend.

---

## What "Premium" Actually Means Here

A few specific design choices to internalize — these are what separates a generic dashboard from something that looks like Vercel:

1. **Near-black background, not slate** — `#0a0a0a` not `#0f172a`. Vercel uses pure dark.
2. **1px borders at low opacity** — borders should be felt, not seen. `border-white/[0.06]` not `border-zinc-800`.
3. **No drop shadows on cards** — flat surfaces, separated by borders only.
4. **Monospace for IDs and numbers** — R001, 4823 TPS — sets a tone of precision.
5. **Tight letter spacing on headers** — `tracking-tight` everywhere.
6. **Subtle hover states** — opacity changes, not color changes.
7. **No emojis, no rounded toy aesthetics** — every corner radius is intentional (`rounded-md` not `rounded-2xl`).
8. **One accent color only** — we'll use a muted blue. Restraint reads as confidence.

---

## What Claude Code Will Build

```
querymind/
└── frontend/
    ├── index.html                          # UPDATED — load Geist font
    ├── tailwind.config.js                  # UPDATED — Geist + custom theme
    ├── package.json                        # UPDATED — add date-fns for relative timestamps
    └── src/
        ├── App.jsx                         # UPDATED — 3-panel layout, new state shape
        ├── index.css                       # UPDATED — Geist font face, scroll polish
        ├── api/
        │   └── chat.js                     # UPDATED — 4 new functions for the new endpoints
        ├── components/
        │   ├── Sidebar.jsx                 # NEW — chat list, new chat button
        │   ├── ChatPanel.jsx               # UPDATED — uses message state from server
        │   ├── InsightPanel.jsx            # UPDATED — premium styling
        │   ├── Chart.jsx                   # UPDATED — colors match new theme
        │   ├── Message.jsx                 # NEW — single message bubble
        │   └── EmptyState.jsx              # NEW — shown when no chat is selected
        └── lib/
            └── format.js                   # NEW — small helpers (relative time, etc.)
```

About 10 files touched. Most updates are styling; the structural changes are in `App.jsx` (new state shape) and the new `Sidebar.jsx`.

---

## Step 1 — Update `package.json`

We need one new dependency: `date-fns` for relative timestamp formatting ("2 minutes ago", "yesterday").

```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "recharts": "^2.13.0",
    "date-fns": "^4.1.0"
  }
}
```

(Keep all existing dependencies; just add `date-fns`.)

---

## Step 2 — `frontend/index.html`

Load Geist font from Vercel's CDN.

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>QueryMind</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
  </head>
  <body class="bg-black">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

---

## Step 3 — `frontend/tailwind.config.js`

Wire up Geist as the default font, define our custom color tokens.

```javascript
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Geist', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'ui-monospace', 'SF Mono', 'monospace'],
      },
      colors: {
        // Our muted blue accent — restrained, professional
        accent: {
          DEFAULT: '#3b82f6',
          hover: '#60a5fa',
          subtle: 'rgba(59, 130, 246, 0.1)',
        },
      },
      animation: {
        'fade-in': 'fadeIn 200ms ease-out',
        'slide-up': 'slideUp 250ms ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
        slideUp: {
          '0%': { opacity: 0, transform: 'translateY(8px)' },
          '100%': { opacity: 1, transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
}
```

---

## Step 4 — `frontend/src/index.css`

Add subtle global styles — better scrollbars, antialiasing, base background.

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html, body, #root {
  height: 100%;
  margin: 0;
  background: #0a0a0a;
  color: #ededed;
}

body {
  font-family: 'Geist', system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  font-feature-settings: 'cv11', 'ss01';
}

/* Custom scrollbars — thin and subtle */
*::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

*::-webkit-scrollbar-track {
  background: transparent;
}

*::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

*::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.1);
}

/* Disable default focus ring; we'll style our own where needed */
*:focus {
  outline: none;
}
```

---

## Step 5 — `frontend/src/lib/format.js`

Small helpers for human-friendly formatting.

```javascript
import { formatDistanceToNow, parseISO } from 'date-fns'

/**
 * "2 minutes ago", "yesterday", etc.
 * Falls back gracefully if the input is malformed.
 */
export function relativeTime(isoString) {
  try {
    return formatDistanceToNow(parseISO(isoString), { addSuffix: true })
  } catch {
    return ''
  }
}
```

---

## Step 6 — `frontend/src/api/chat.js`

Replace the old single-function file with 4 functions matching the new endpoints.

```javascript
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
```

---

## Step 7 — `frontend/src/components/Sidebar.jsx`

The new left sidebar — chat list + "New chat" button.

```jsx
import { relativeTime } from '../lib/format'

export default function Sidebar({ chats, activeChatId, onSelectChat, onNewChat, isLoading }) {
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
          return (
            <button
              key={chat.chat_id}
              onClick={() => onSelectChat(chat.chat_id)}
              className={`w-full text-left px-4 py-3 transition-colors border-l-2 ${
                isActive
                  ? 'bg-white/[0.04] border-l-accent'
                  : 'border-l-transparent hover:bg-white/[0.02]'
              }`}
            >
              <div className={`text-sm truncate ${isActive ? 'text-white' : 'text-white/80'}`}>
                {chat.title}
              </div>
              <div className="text-[11px] text-white/40 mt-0.5 font-mono">
                {relativeTime(chat.updated_at)}
              </div>
            </button>
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
```

---

## Step 8 — `frontend/src/components/Message.jsx`

A single message in the chat panel. Extracting this into its own component keeps `ChatPanel` clean.

```jsx
export default function Message({ role, content }) {
  const isUser = role === 'user'

  return (
    <div className={`animate-slide-up ${isUser ? 'flex justify-end' : 'flex justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-lg px-4 py-3 text-sm leading-relaxed ${
          isUser
            ? 'bg-white/[0.06] text-white border border-white/[0.06]'
            : 'text-white/90'
        }`}
      >
        <div className="text-[10px] uppercase tracking-wider font-mono mb-1.5 text-white/40">
          {isUser ? 'You' : 'Assistant'}
        </div>
        <div className="whitespace-pre-wrap">{content}</div>
      </div>
    </div>
  )
}
```

---

## Step 9 — `frontend/src/components/EmptyState.jsx`

What shows when no chat is selected, or a new chat has no messages yet.

```jsx
const SUGGESTIONS = [
  'Tell me the summary of my last benchmark',
  'Compare runs R007 and R008',
  'Which run had the worst tail latency?',
  'Is performance improving over the last 5 runs?',
]

export default function EmptyState({ onSuggestion, disabled }) {
  return (
    <div className="h-full flex items-center justify-center px-8">
      <div className="max-w-md text-center animate-fade-in">
        <div className="text-2xl font-medium tracking-tight mb-2">
          Ask anything about your benchmarks
        </div>
        <div className="text-sm text-white/50 mb-8">
          QueryMind analyzes performance data and surfaces insights you'd otherwise hunt for in tables.
        </div>

        <div className="space-y-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => onSuggestion(s)}
              disabled={disabled}
              className="w-full text-left px-4 py-3 text-sm rounded-md bg-white/[0.02] hover:bg-white/[0.05] border border-white/[0.06] hover:border-white/[0.12] text-white/80 hover:text-white transition-all disabled:opacity-50"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
```

---

## Step 10 — `frontend/src/components/ChatPanel.jsx`

The middle panel — messages + input. Notice we no longer manage suggested chips here (they moved to `EmptyState`).

```jsx
import { useState, useRef, useEffect } from 'react'
import Message from './Message'
import EmptyState from './EmptyState'

export default function ChatPanel({ messages, onSend, isLoading, hasActiveChat }) {
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
              <Message key={msg.message_id} role={msg.role} content={msg.content} />
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
              className="px-4 py-3 rounded-md bg-accent hover:bg-accent-hover text-white text-sm font-medium transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              Send
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
```

---

## Step 11 — `frontend/src/components/InsightPanel.jsx`

The right panel — now styled to match. Same data shape from the backend.

```jsx
import Chart from './Chart'

export default function InsightPanel({ latestResponse, isLoading }) {
  if (isLoading && !latestResponse) {
    return (
      <div className="h-full flex items-center justify-center text-white/40">
        <div className="text-sm font-mono">analyzing...</div>
      </div>
    )
  }

  if (!latestResponse) {
    return (
      <div className="h-full flex flex-col items-center justify-center px-8 text-center">
        <div className="text-sm text-white/40 mb-1">
          Insights appear here
        </div>
        <div className="text-xs text-white/30 font-mono">
          waiting for first message
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col gap-4 p-6 overflow-y-auto animate-fade-in">
      {/* Insight card */}
      <div className="bg-white/[0.02] border border-white/[0.06] rounded-lg p-5">
        <div className="text-[10px] uppercase tracking-wider font-mono text-white/40 mb-3">
          Insight
        </div>
        <div className="text-white/90 leading-relaxed text-[15px]">
          {latestResponse.insight}
        </div>
      </div>

      {/* Chart card */}
      {latestResponse.chart_type !== 'none' && latestResponse.chart_data?.length > 0 && (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-lg p-5 flex-1 min-h-[340px]">
          <div className="text-[10px] uppercase tracking-wider font-mono text-white/40 mb-4">
            {latestResponse.chart_type === 'line' ? 'Trend' : 'Distribution'}
          </div>
          <Chart
            chartType={latestResponse.chart_type}
            chartData={latestResponse.chart_data}
          />
        </div>
      )}
    </div>
  )
}
```

---

## Step 12 — `frontend/src/components/Chart.jsx`

Tweak the chart colors to match the new theme.

```jsx
import {
  BarChart, Bar,
  LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

export default function Chart({ chartType, chartData }) {
  if (chartType === 'none' || !chartData || chartData.length === 0) {
    return null
  }

  const axisColor = 'rgba(255, 255, 255, 0.4)'
  const gridColor = 'rgba(255, 255, 255, 0.06)'
  const barColor = '#3b82f6'
  const lineColor = '#3b82f6'

  const tooltipStyle = {
    background: '#0a0a0a',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    borderRadius: '6px',
    color: '#fafafa',
    fontSize: '12px',
    fontFamily: 'Geist Mono, monospace',
  }

  if (chartType === 'bar') {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
          <CartesianGrid stroke={gridColor} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" stroke={axisColor} fontSize={11} tickLine={false} axisLine={false} />
          <YAxis stroke={axisColor} fontSize={11} tickLine={false} axisLine={false} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'rgba(255, 255, 255, 0.03)' }} />
          <Bar dataKey="value" fill={barColor} radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    )
  }

  if (chartType === 'line') {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 10, right: 10, bottom: 10, left: 0 }}>
          <CartesianGrid stroke={gridColor} strokeDasharray="3 3" vertical={false} />
          <XAxis dataKey="name" stroke={axisColor} fontSize={11} tickLine={false} axisLine={false} />
          <YAxis stroke={axisColor} fontSize={11} tickLine={false} axisLine={false} />
          <Tooltip contentStyle={tooltipStyle} cursor={{ stroke: 'rgba(255, 255, 255, 0.1)' }} />
          <Line
            type="monotone"
            dataKey="value"
            stroke={lineColor}
            strokeWidth={2}
            dot={{ fill: lineColor, r: 3 }}
            activeDot={{ r: 5 }}
          />
        </LineChart>
      </ResponsiveContainer>
    )
  }

  return null
}
```

---

## Step 13 — `frontend/src/App.jsx`

The biggest rewrite. New state shape, new layout, new data flow.

```jsx
import { useState, useEffect, useCallback } from 'react'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import InsightPanel from './components/InsightPanel'
import { createChat, listChats, getMessages, sendMessage } from './api/chat'

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
        />
      </div>

      {/* Insight panel */}
      <div className="w-[440px] flex-shrink-0">
        <InsightPanel latestResponse={latestResponse} isLoading={isLoading} />
      </div>
    </div>
  )
}
```

---

## Step-by-Step Instructions for Claude Code

Hand this file to Claude Code with:

```
Please read PHASE_6B.md and implement the premium UI redesign.

Work in this order:
1. Update package.json (add date-fns), ask before running npm install
2. Update index.html (Geist font)
3. Update tailwind.config.js
4. Update src/index.css
5. Create src/lib/format.js
6. Replace src/api/chat.js entirely
7. Create src/components/Sidebar.jsx
8. Create src/components/Message.jsx
9. Create src/components/EmptyState.jsx
10. Replace src/components/ChatPanel.jsx
11. Replace src/components/InsightPanel.jsx
12. Replace src/components/Chart.jsx
13. Replace src/App.jsx

Use the exact code from the spec.

After all files are in place, stop. I'll run npm install and start the dev server.
```

---

## How to Run It (Your Steps)

### 1. Install the new dependency

```bash
cd frontend
npm install
```

### 2. Make sure the backend is still running

In a separate terminal:
```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 3. Start the frontend

```bash
cd frontend
npm run dev
```

Open http://localhost:5173.

### 4. Test the full flow

1. **Empty state** — you should see "Ask anything about your benchmarks" with 4 suggestion buttons.
2. **Click a suggestion** — a chat gets auto-created, the message gets sent, and you see the assistant response.
3. **Watch the sidebar** — the new chat appears at the top, and after the first message, the title updates from "New chat" to something Gemini generated (e.g. "Latest benchmark summary").
4. **Ask a follow-up** — like "How does it compare to R005?" — the response should reference the prior context.
5. **Click "New chat"** in the sidebar — fresh empty state, the sidebar shows both chats now.
6. **Click the previous chat** — messages load, latest insight reappears on the right.
7. **Refresh the browser** — everything persists. Chats, messages, insights all come back from the database.

---

## What You Should Understand After This Phase

### 1. The state shape mirrors what the backend stores
We moved from "messages live in React state" to "messages live in Postgres, React just renders them." The frontend now treats the backend as the source of truth — that's the real-app pattern.

### 2. Optimistic updates make the UI feel fast
When you click Send, the user message appears **immediately** — before the backend has even confirmed. Then we replace it with the real one when the response arrives. If the server is slow, the user still feels in control.

### 3. Why we don't refetch messages after sending
The response already includes both `user_message` and `assistant_message`. We append them to local state directly. A naive implementation would call `getMessages()` again — but that's an unnecessary round trip and would cause a flicker.

### 4. The 3-panel layout serves three different time horizons
- **Sidebar**: long-term — every chat you've ever had
- **Chat panel**: medium-term — the conversation as it builds
- **Insight panel**: short-term — only the latest answer, with its visualization

Each panel has a clear job. None of them tries to be all three.

### 5. The aesthetic isn't decorative — it signals care
Hairline borders, sentence case, monospace numerals, animations. None of these are necessary for the app to function. But together they signal "this was made carefully." That's what separates a tool people enjoy using from one they tolerate.

### 6. Component composition pays off
Look at how clean `App.jsx` is despite all the new functionality. That's because we extracted `Sidebar`, `Message`, `EmptyState` into their own files. Each one has one job. When you want to change the empty state copy, you don't have to wade through 300 lines of code — you open `EmptyState.jsx`.

---

## Common Issues

| Symptom | Likely Cause |
|---|---|
| Font looks generic / wrong | Browser didn't load Geist — check Network tab in DevTools, look for `googleapis.com/css2` |
| Sidebar is blank | Backend isn't running, or `listChats()` is failing — check console |
| Click "New chat" does nothing | Check Network tab — `POST /api/chats` might be 500'ing on the backend |
| Sidebar doesn't refresh after send | `refreshChats()` failed silently — check console |
| Message text wraps weirdly | Make sure you're using `whitespace-pre-wrap` (not `pre-line`) |
| Chart colors off | Make sure tailwind.config.js was updated and Vite was restarted |
| Layout breaks on narrow window | The 3-panel layout assumes desktop; mobile responsive design is a stretch goal |

---

## Done?

When you've verified:
- [ ] The UI looks distinctly different from Phase 5 — premium dark theme, Geist font, hairline borders
- [ ] You can create new chats and switch between them
- [ ] Chat titles auto-generate after first message
- [ ] Refreshing the browser preserves everything
- [ ] Follow-up questions work in context (the killer feature)
- [ ] Suggested questions in the empty state work
- [ ] Loading state shows the animated dots
- [ ] The right panel updates whenever you switch chats

You're done. **QueryMind is complete.**

---

## What You Just Built

Take stock. End-to-end, you now have:

1. A **Postgres-backed persistence layer** with chat history, messages, and benchmark data
2. A **read-only analysis layer** with 5 tool functions
3. An **LLM orchestration layer** that runs the two-round tool-calling loop with multi-turn context
4. An **HTTP API layer** with FastAPI, CORS, lifespan management, and proper request/response validation
5. A **premium frontend** with sidebar navigation, optimistic updates, smooth animations, and a clean design system

This is genuinely a small production-quality app. The architecture maps directly to PAS AI Insights at AWS — different services in each layer, same shape.

When you sit down to build the AWS version, you'll be doing it for the second time. That's the whole point of building this POC first.

Go demo it to someone. 🚀