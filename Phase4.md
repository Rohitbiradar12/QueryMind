# Phase 4 — FastAPI Backend (HTTP API)

## Goal of This Phase

Wrap everything we've built so far in an **HTTP API** so a frontend (or anyone else) can talk to it.

By the end of this phase, you'll have a running server on `http://localhost:8000` with a single endpoint:

```
POST /api/chat
Body: { "message": "Tell me the summary of my last benchmark" }
Returns: { "insight": "...", "chart_type": "bar", "chart_data": [...] }
```

You'll test it from the browser, from `curl`, and via FastAPI's auto-generated docs page.

**Still no UI** — that's Phase 5. This phase is about making the AI layer accessible over HTTP.

---

## Why a Backend API at All?

Up to now, `test_gemini.py` was a standalone Python script. It worked, but:

- Only one person can use it at a time (whoever runs the script)
- A browser can't run Python — it needs an HTTP endpoint
- No request lifecycle management (auth, logging, rate limiting can live here)
- The DB connection pool needs to be reused across many requests, not torn down each call

FastAPI gives us all of that for free. We add ~50 lines of code and now any HTTP client (browser, mobile app, curl, Postman) can use our AI layer.

---

## What Claude Code Will Build

```
querymind/
├── backend/
│   ├── models.py              # NEW — Pydantic request/response schemas
│   ├── main.py                # NEW — FastAPI app, lifespan, /api/chat endpoint
│   └── requirements.txt       # UPDATED — add fastapi, uvicorn
```

Two new files + one updated file. The existing files (`database.py`, `tools.py`, `gemini_client.py`, `tool_schemas.py`) stay untouched.

This is the **layered architecture** paying off — the HTTP layer doesn't need to change any of the layers below it.

---

## File 1: Updated `backend/requirements.txt`

```
asyncpg==0.30.0
python-dotenv==1.0.1
google-genai==0.3.0
fastapi==0.115.0
uvicorn[standard]==0.32.0
```

The `[standard]` extras on uvicorn give us:
- Automatic reload on code changes (during development)
- Better logging
- HTTP/1.1 + WebSocket support (not used now, but useful later)

---

## File 2: `backend/models.py` — Request/Response Schemas

Pydantic models that define what the API accepts and returns. FastAPI uses these for automatic validation, type checking, and OpenAPI docs.

```python
"""
Pydantic models for the QueryMind HTTP API.

FastAPI uses these to:
1. Validate incoming request bodies (rejects malformed JSON automatically)
2. Validate outgoing responses (catches bugs early)
3. Generate OpenAPI/Swagger docs at /docs
"""

from typing import Literal, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """What the client sends to /api/chat."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The user's natural language question",
    )


class ChartDataPoint(BaseModel):
    """A single point in a chart."""
    name: str
    value: float


class ChatResponse(BaseModel):
    """What /api/chat returns."""
    insight: str = Field(..., description="Human-readable analysis from Gemini")
    chart_type: Literal["bar", "line", "none"] = Field(
        ...,
        description="What kind of chart the UI should render"
    )
    chart_data: list[ChartDataPoint | dict[str, Any]] = Field(
        default_factory=list,
        description="Data points for the chart"
    )
```

### Why use Pydantic instead of plain dicts?

Without it, you'd have to manually check `if "message" not in request_body: raise BadRequest`. With Pydantic, FastAPI does this automatically. Send a request missing the `message` field, and FastAPI returns a clean 422 error explaining what's wrong — you write zero validation code.

It also generates the Swagger UI at `/docs` for free, which makes testing the API much easier.

---

## File 3: `backend/main.py` — The FastAPI App

This is the only file that knows about HTTP. Everything else stays clean.

```python
"""
QueryMind FastAPI Backend.

Single endpoint:
  POST /api/chat   — natural language question → insight + chart data

Architecture:
  HTTP request  →  FastAPI route  →  gemini_client.run_conversation()
                                       │
                                       ├── Gemini API
                                       └── tools.py → database.py → Postgres
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import init_pool, close_pool
from gemini_client import run_conversation
from models import ChatRequest, ChatResponse


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan — runs once at startup, once at shutdown
# ─────────────────────────────────────────────────────────────────────────────
# We use this to manage the asyncpg connection pool:
#   - On startup: create the pool (opens initial DB connections)
#   - On shutdown: close the pool cleanly
#
# Without this, every request would open/close a new connection (slow), or
# the pool would never get closed properly on Ctrl+C.
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("[Startup] Initializing database pool...")
    await init_pool()
    print("[Startup] Ready.")
    yield
    # Shutdown
    print("[Shutdown] Closing database pool...")
    await close_pool()
    print("[Shutdown] Done.")


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="QueryMind API",
    description="AI-powered natural language insights over benchmark data",
    version="0.1.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────────────────────────────────────
# CORS — Cross-Origin Resource Sharing
# ─────────────────────────────────────────────────────────────────────────────
# By default browsers BLOCK requests from one origin to another for security.
# Our React frontend will run on http://localhost:5173 (Vite default), but
# this backend runs on http://localhost:8000 — different origins.
#
# Without this middleware, the browser would refuse to send requests from the
# frontend. We explicitly allow the Vite dev server's origin.
# ─────────────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    """Health check — confirms the server is alive."""
    return {"status": "ok", "service": "querymind"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main endpoint. Takes a natural language question, returns an insight + chart.

    FastAPI automatically:
      - Parses the JSON body
      - Validates it against ChatRequest
      - Returns 422 if validation fails
    """
    try:
        result = await run_conversation(request.message)
        return ChatResponse(**result)
    except Exception as e:
        # In production you'd log this properly and return a sanitized error.
        # For a POC, surface the message so debugging is easy.
        print(f"[Error] {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Notes on what's happening here

**`lifespan`** — Replaces the older `@app.on_event("startup")` pattern. It guarantees `init_pool()` runs once before any requests, and `close_pool()` runs on graceful shutdown.

**`response_model=ChatResponse`** — Tells FastAPI to validate the response before sending. If `run_conversation` returns something missing `insight`, you'll get a clear error instead of a confusing client-side bug later.

**`try/except`** — Any exception inside `run_conversation` (DB down, Gemini timeout, etc.) gets turned into a 500 response with the error message. For a POC, that's fine. In production you'd hide error details and log them server-side.

---

## Step-by-Step Instructions for Claude Code

Hand `PHASE_4.md` to Claude Code with this prompt:

```
Please read PHASE_4.md and build Phase 4 of the QueryMind project.

Create/update these files:
1. Update backend/requirements.txt to add fastapi and uvicorn[standard]
2. Create backend/models.py
3. Create backend/main.py

Use the exact code from the spec.

After all files are created, stop. I will install dependencies and 
start the server myself.
```

---

## How to Run It (Your Step)

### 1. Install the new dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Start the server
```bash
uvicorn main:app --reload --port 8000
```

You should see:
```
[Startup] Initializing database pool...
[Startup] Ready.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

The `--reload` flag auto-restarts the server when you change code. Useful during development; you'd disable it in production.

### 3. Verify it works — three ways

**(a) From the browser, hit the health check:**
Open http://localhost:8000/ — should show `{"status":"ok","service":"querymind"}`.

**(b) FastAPI's auto-generated docs:**
Open http://localhost:8000/docs — you'll see a Swagger UI. Click `POST /api/chat`, then "Try it out", paste this body:
```json
{ "message": "Tell me the summary of my last benchmark" }
```
Click "Execute". You should get a 200 response with insight + chart data.

**(c) From the terminal with curl:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Compare runs R007 and R008"}'
```

If all three work, the backend is solid.

---

## What You Should Understand After This Phase

### 1. Why this layer is thin
`main.py` is short on purpose. It does three things: parse the request, call `run_conversation`, return the response. All real logic lives in the layers below. **If you find yourself writing complex code in the API layer, you're putting it in the wrong place.**

### 2. What CORS actually is and why it matters
Browsers enforce a security rule: by default, code on `http://localhost:5173` (your frontend) cannot send requests to `http://localhost:8000` (your backend). They're different origins. The browser would silently block the request before it even leaves.

The `CORSMiddleware` tells the browser: "yes, the backend explicitly allows this origin." It does this by adding HTTP headers like `Access-Control-Allow-Origin: http://localhost:5173` to responses.

CORS catches almost every junior developer off-guard the first time. Now you know.

### 3. Why lifespan instead of opening a pool per request
DB pool creation is expensive (~100-500ms). If you re-created it for every HTTP request, the API would be unusably slow. The lifespan pattern creates it once at startup and shares it across all requests. Same pool, many concurrent users.

### 4. Why Pydantic validation matters
Without it, every endpoint would need its own `if request_body is missing X: return 400` boilerplate. Pydantic does it once, declaratively. You define the shape; FastAPI enforces it.

### 5. The "API layer" is just one possible interface
Right now we expose this AI via HTTP. Tomorrow we could expose the same `run_conversation` function via:
- A CLI (`querymind ask "tell me about R005"`)
- A Slack bot
- A scheduled job that emails reports

The HTTP API is **one consumer** of `run_conversation`. The layered design makes that easy.

---

## Common Issues

| Symptom | Likely Cause |
|---|---|
| `ModuleNotFoundError: No module named 'main'` | You're not in the `backend/` directory when running uvicorn |
| `address already in use` | Port 8000 is taken — kill the process or use `--port 8001` |
| `relation does not exist` | DB not seeded — re-run `seed.sql` |
| `422 Unprocessable Entity` from `/api/chat` | Missing `message` field or wrong JSON shape — that's Pydantic catching a bad request |
| `500 Internal Server Error` | Check the terminal where uvicorn is running — exception will be printed |
| Browser blocks request with CORS error | Check origin matches `http://localhost:5173` exactly (not `127.0.0.1`) |

---

## Done?

Before moving on, confirm:
- [ ] `uvicorn main:app --reload --port 8000` starts cleanly
- [ ] http://localhost:8000/ returns the health check JSON
- [ ] http://localhost:8000/docs renders the Swagger UI
- [ ] You sent a request via /docs and got a real insight back
- [ ] You sent a curl request and got an insight back
- [ ] You can explain CORS, lifespan, and why Pydantic matters

When all that's true, come back and I'll send **Phase 5: React UI** — the final phase. We'll build a clean chat interface that talks to your `/api/chat` endpoint and renders the charts.