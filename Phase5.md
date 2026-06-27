# Phase 5 — React UI (The Final Piece)

## Goal of This Phase

Build a clean, two-panel React app that talks to your `/api/chat` endpoint and renders Gemini's insights as text + charts. By the end of this phase, you'll have a working full-stack app:

- Type a natural language question in the left panel
- See the conversation history build up
- Watch the right panel render an insight card + a chart (bar or line) based on Gemini's response

This is the last phase. Once it works, QueryMind is complete and you've built the full pattern you'll replicate at AWS.

---

## What the App Looks Like

```
┌────────────────────────────┬──────────────────────────────────────┐
│                            │                                      │
│       Chat Panel (40%)     │      Insight Panel (60%)             │
│                            │                                      │
│  ┌──────────────────────┐  │  ┌────────────────────────────────┐  │
│  │ user: tell me about  │  │  │                                │  │
│  │ my last benchmark    │  │  │  INSIGHT                       │  │
│  ├──────────────────────┤  │  │  Your latest run R010 shows    │  │
│  │ assistant: Your      │  │  │  healthy throughput at 5000 TPS│  │
│  │ latest run R010...   │  │  │  with P99 latency around 56ms. │  │
│  └──────────────────────┘  │  │                                │  │
│                            │  └────────────────────────────────┘  │
│  Suggested chips:          │                                      │
│  [ Last benchmark ]        │  ┌────────────────────────────────┐  │
│  [ Compare R007 R008 ]     │  │   [ bar chart of P50/P95/P99 ] │  │
│  [ Show trends ]           │  │                                │  │
│                            │  └────────────────────────────────┘  │
│  ┌──────────────────────┐  │                                      │
│  │ type a question... 📤│  │                                      │
│  └──────────────────────┘  │                                      │
└────────────────────────────┴──────────────────────────────────────┘
```

---

## Stack

- **Vite** — fast build tool, modern React scaffolding
- **React 18** — UI library (functional components + hooks)
- **Tailwind CSS** — utility-first styling, dark theme
- **Recharts** — chart library for rendering BarChart and LineChart
- **Plain `fetch`** — no Axios needed, the browser's built-in `fetch` works fine

---

## What Claude Code Will Build

```
querymind/
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── index.html
    └── src/
        ├── main.jsx                       # React entry point
        ├── App.jsx                        # Top-level layout (two panels)
        ├── index.css                      # Tailwind directives
        ├── api/
        │   └── chat.js                    # fetch wrapper for /api/chat
        └── components/
            ├── ChatPanel.jsx              # Left panel: messages + input + chips
            ├── InsightPanel.jsx           # Right panel: insight card + chart
            └── Chart.jsx                  # Conditional bar/line/empty
```

About 10 files. Don't be alarmed by the count — most are tiny config files Vite needs.

---

## Step-by-Step Instructions for Claude Code

This phase has a lot of files. Give Claude Code this prompt:

```
Please read PHASE_5.md and build Phase 5 of the QueryMind project.

Work in this order:
1. Scaffold the frontend folder with Vite (React + JS, NOT TypeScript)
2. Install Tailwind CSS and configure it
3. Install recharts
4. Create the API helper (src/api/chat.js)
5. Create the component files (ChatPanel, InsightPanel, Chart)
6. Wire up App.jsx
7. Wire up main.jsx
8. Update index.html title

Use the exact code from the spec. For npm install, ask me before running it.

After all files are in place and dependencies are installed, tell me how to 
start the dev server and I'll test it.
```

---

## File 1: `frontend/package.json`

This is what Claude Code generates when you scaffold with Vite. The key dependencies you need:

```json
{
  "name": "querymind-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "recharts": "^2.13.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.17",
    "vite": "^6.0.5"
  }
}
```

---

## File 2: `frontend/vite.config.js`

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
  },
})
```

---

## File 3: `frontend/tailwind.config.js`

```javascript
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        mono: ['ui-monospace', 'SF Mono', 'Monaco', 'monospace'],
      },
    },
  },
  plugins: [],
}
```

---

## File 4: `frontend/postcss.config.js`

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

---

## File 5: `frontend/index.html`

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>QueryMind</title>
  </head>
  <body class="bg-zinc-950">
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

---

## File 6: `frontend/src/index.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

html, body, #root {
  height: 100%;
  margin: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
```

---

## File 7: `frontend/src/main.jsx`

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

---

## File 8: `frontend/src/api/chat.js`

The HTTP wrapper. One function — calls your FastAPI backend.

```javascript
/**
 * Sends a user message to the QueryMind backend and returns the AI response.
 *
 * The backend lives at http://localhost:8000/api/chat. The browser's fetch()
 * sends a POST with JSON body and returns the parsed JSON response.
 *
 * If the request fails (network error, 500 from backend, etc.), this function
 * throws — the caller is responsible for catching and showing an error state.
 */
export async function sendMessage(message) {
  const response = await fetch('http://localhost:8000/api/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new Error(`Backend error (${response.status}): ${errorText}`)
  }

  return response.json()
}
```

---

## File 9: `frontend/src/components/Chart.jsx`

Renders the chart based on the `chart_type` from the backend response.

```jsx
import {
  BarChart, Bar,
  LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts'

/**
 * Renders a chart based on type + data from the backend.
 *
 * chart_type === "bar"  → BarChart
 * chart_type === "line" → LineChart
 * chart_type === "none" → empty placeholder
 */
export default function Chart({ chartType, chartData }) {
  if (chartType === 'none' || !chartData || chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-zinc-600 text-sm">
        No chart for this response
      </div>
    )
  }

  // Tailwind's zinc-400 = #a1a1aa, zinc-700 = #3f3f46
  const axisColor = '#a1a1aa'
  const gridColor = '#3f3f46'
  const barColor = '#60a5fa'   // blue-400
  const lineColor = '#34d399'  // emerald-400

  if (chartType === 'bar') {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
          <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />
          <XAxis dataKey="name" stroke={axisColor} fontSize={12} />
          <YAxis stroke={axisColor} fontSize={12} />
          <Tooltip
            contentStyle={{
              background: '#18181b',
              border: '1px solid #3f3f46',
              borderRadius: '6px',
              color: '#fafafa',
            }}
          />
          <Bar dataKey="value" fill={barColor} radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    )
  }

  if (chartType === 'line') {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
          <CartesianGrid stroke={gridColor} strokeDasharray="3 3" />
          <XAxis dataKey="name" stroke={axisColor} fontSize={12} />
          <YAxis stroke={axisColor} fontSize={12} />
          <Tooltip
            contentStyle={{
              background: '#18181b',
              border: '1px solid #3f3f46',
              borderRadius: '6px',
              color: '#fafafa',
            }}
          />
          <Line
            type="monotone"
            dataKey="value"
            stroke={lineColor}
            strokeWidth={2}
            dot={{ fill: lineColor, r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    )
  }

  return null
}
```

---

## File 10: `frontend/src/components/InsightPanel.jsx`

The right panel — shows the most recent insight + chart.

```jsx
import Chart from './Chart'

/**
 * Displays the latest assistant response: insight text + chart.
 * When there's no response yet, shows an empty state.
 */
export default function InsightPanel({ latestResponse, isLoading }) {
  if (isLoading) {
    return (
      <div className="h-full flex items-center justify-center text-zinc-500">
        <div className="animate-pulse">Analyzing benchmark data...</div>
      </div>
    )
  }

  if (!latestResponse) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-zinc-600">
        <div className="text-lg mb-2">Ask a question to get started</div>
        <div className="text-sm text-zinc-700">
          Try the suggestions on the left, or type your own
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col gap-6 p-6 overflow-y-auto">
      {/* Insight card */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5">
        <div className="text-xs uppercase tracking-wider text-zinc-500 mb-2">
          Insight
        </div>
        <div className="text-zinc-100 leading-relaxed">
          {latestResponse.insight}
        </div>
      </div>

      {/* Chart card */}
      <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-5 flex-1 min-h-[340px]">
        <div className="text-xs uppercase tracking-wider text-zinc-500 mb-4">
          Visualization
        </div>
        <Chart
          chartType={latestResponse.chart_type}
          chartData={latestResponse.chart_data}
        />
      </div>
    </div>
  )
}
```

---

## File 11: `frontend/src/components/ChatPanel.jsx`

The left panel — message history, suggested chips, input box.

```jsx
import { useState, useRef, useEffect } from 'react'

const SUGGESTED_QUERIES = [
  'Tell me the summary of my last benchmark',
  'Compare runs R007 and R008',
  'Is performance improving over the last 5 runs?',
  'Show me all available runs',
]

export default function ChatPanel({ messages, onSend, isLoading }) {
  const [input, setInput] = useState('')
  const messagesEndRef = useRef(null)

  // Auto-scroll to newest message whenever messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = () => {
    const trimmed = input.trim()
    if (!trimmed || isLoading) return
    onSend(trimmed)
    setInput('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleChipClick = (query) => {
    if (isLoading) return
    onSend(query)
  }

  return (
    <div className="h-full flex flex-col border-r border-zinc-800">
      {/* Header */}
      <div className="px-5 py-4 border-b border-zinc-800">
        <div className="text-zinc-100 font-medium">QueryMind</div>
        <div className="text-xs text-zinc-500 mt-0.5">
          Natural language insights over your benchmarks
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.length === 0 && (
          <div className="text-zinc-600 text-sm">
            No messages yet. Try a suggestion below.
          </div>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={`rounded-lg p-3 ${
              msg.role === 'user'
                ? 'bg-zinc-800 text-zinc-100 ml-6'
                : 'bg-zinc-900 border border-zinc-800 text-zinc-200 mr-6'
            }`}
          >
            <div className="text-xs text-zinc-500 mb-1 uppercase tracking-wider">
              {msg.role}
            </div>
            <div className="text-sm leading-relaxed whitespace-pre-wrap">
              {msg.content}
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="bg-zinc-900 border border-zinc-800 rounded-lg p-3 mr-6">
            <div className="text-xs text-zinc-500 mb-1 uppercase tracking-wider">
              assistant
            </div>
            <div className="text-sm text-zinc-500 animate-pulse">Thinking…</div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested chips */}
      <div className="px-5 py-3 border-t border-zinc-800">
        <div className="text-xs text-zinc-500 mb-2 uppercase tracking-wider">
          Suggestions
        </div>
        <div className="flex flex-wrap gap-2">
          {SUGGESTED_QUERIES.map((q) => (
            <button
              key={q}
              onClick={() => handleChipClick(q)}
              disabled={isLoading}
              className="text-xs px-3 py-1.5 rounded-full bg-zinc-800 hover:bg-zinc-700 text-zinc-300 disabled:opacity-50 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="p-5 border-t border-zinc-800">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            placeholder="Ask about your benchmarks…"
            className="flex-1 bg-zinc-900 border border-zinc-800 rounded-lg px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 focus:outline-none focus:border-zinc-600"
          />
          <button
            onClick={handleSubmit}
            disabled={isLoading || !input.trim()}
            className="px-4 py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  )
}
```

---

## File 12: `frontend/src/App.jsx`

The top-level component — wires everything together and owns the state.

```jsx
import { useState } from 'react'
import ChatPanel from './components/ChatPanel'
import InsightPanel from './components/InsightPanel'
import { sendMessage } from './api/chat'

export default function App() {
  // messages = full conversation history (for the chat panel)
  const [messages, setMessages] = useState([])
  // latestResponse = most recent assistant response (drives the right panel chart)
  const [latestResponse, setLatestResponse] = useState(null)
  const [isLoading, setIsLoading] = useState(false)

  const handleSend = async (text) => {
    // Add user message immediately so the UI feels responsive
    setMessages((prev) => [...prev, { role: 'user', content: text }])
    setIsLoading(true)

    try {
      const response = await sendMessage(text)
      // Add assistant text to chat
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.insight },
      ])
      // Drive the right panel with the full response (includes chart data)
      setLatestResponse(response)
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${err.message}` },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="h-full flex bg-zinc-950 text-zinc-100">
      <div className="w-2/5 min-w-[380px]">
        <ChatPanel
          messages={messages}
          onSend={handleSend}
          isLoading={isLoading}
        />
      </div>
      <div className="flex-1">
        <InsightPanel
          latestResponse={latestResponse}
          isLoading={isLoading}
        />
      </div>
    </div>
  )
}
```

---

## How to Run It (Your Step)

### 1. Install dependencies

```bash
cd frontend
npm install
```

This takes a minute. It installs React, Vite, Tailwind, Recharts, and all their dependencies.

### 2. Make sure your backend is running

In a **separate terminal**, start the FastAPI server (from Phase 4):

```bash
cd backend
uvicorn main:app --reload --port 8000
```

You should see `[Startup] Ready.`

### 3. Start the frontend dev server

Back in the frontend terminal:

```bash
npm run dev
```

Vite will print:
```
  VITE ready
  ➜  Local:   http://localhost:5173/
```

### 4. Open the app

Open http://localhost:5173 in your browser. You should see the dark two-panel layout.

### 5. Test it

Click one of the suggested chips, or type:
> Tell me the summary of my last benchmark

Within a couple of seconds:
- The user message appears in the left panel
- "Thinking…" pulses while the backend works
- The assistant's text response appears in the chat history
- The right panel updates with the insight card + a bar chart showing P50/P95/P99 latency

Try a few more:
- *"Compare runs R007 and R008"* → bar chart with grouped throughput
- *"Is performance improving over the last 5 runs?"* → line chart over time
- *"Show me all my runs"* → no chart (empty state on the right)

---

## What You Should Understand After This Phase

### 1. Why we split into multiple components
- `App.jsx` owns **state** (messages, loading, latest response)
- `ChatPanel.jsx` is **presentational** — it takes props and emits events via `onSend`
- `InsightPanel.jsx` is also presentational
- `Chart.jsx` only knows how to render one of three chart types

This separation is called **container/presentational pattern**. State lives at the top. Components just render whatever they're given. Easy to test, easy to swap implementations.

### 2. Why the frontend uses `fetch` and not a fancy data layer
For a POC, `fetch` is fine. As complexity grows (caching, retries, optimistic updates), teams often add libraries like React Query or SWR. We don't need that here.

### 3. Why the two panels look at slightly different data
- `ChatPanel` shows **all messages** (full history) — that's the chat experience
- `InsightPanel` shows **only the latest response** — because the chart represents "what's the current insight". Older charts would clutter the right panel without adding value.

This is a real design decision: not every piece of state should be shown everywhere. Pick what each panel is for.

### 4. Why CORS finally pays off
Your frontend at `localhost:5173` is calling your backend at `localhost:8000`. Without the CORS middleware you added in Phase 4, the browser would silently block this. Now it works because Phase 4's `allow_origins=["http://localhost:5173"]` lets it through.

### 5. The whole stack in one sentence
> User types in the React UI → fetch sends POST to FastAPI → FastAPI calls run_conversation → Gemini decides tool → tools.py queries Postgres → result back to Gemini → Gemini's JSON insight comes back through FastAPI → React renders insight + chart.

You built every step of that. End to end.

---

## Common Issues

| Symptom | Likely Cause |
|---|---|
| Blank page, console error `Failed to fetch` | Backend isn't running on port 8000 |
| CORS error in browser console | Backend's `allow_origins` doesn't match (must be `http://localhost:5173` exactly) |
| `npm run dev` fails with module errors | Run `npm install` again, or delete `node_modules` and reinstall |
| Tailwind classes do nothing | Check `tailwind.config.js` content paths include `./src/**/*.{js,jsx}` |
| Chart renders blank | Open browser dev tools — check the `chart_data` shape in the network response |
| Loading state never ends | Backend crashed mid-request — check the uvicorn terminal for the error |

---

## Done?

Before declaring victory, confirm:
- [ ] `npm run dev` starts the Vite server cleanly
- [ ] http://localhost:5173 loads the two-panel UI
- [ ] You can send a question and see it answered with insight + chart
- [ ] The 4 suggested chips all work
- [ ] Bar charts render for single-run and A/B queries
- [ ] Line charts render for trend queries
- [ ] You can explain the data flow end-to-end without looking at the code
 