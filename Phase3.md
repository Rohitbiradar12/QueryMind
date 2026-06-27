# Phase 3 — Gemini Tool Calling (The Core Pattern)

## Goal of This Phase

Wire up Gemini so it can decide which of your 5 query functions to call based on a user's natural language question. By the end of this phase, you'll have a working script where you can type:

```
"Tell me the summary of my last benchmark"
```

…and Gemini will:
1. Decide it needs to call `get_latest_run_metrics()`
2. Wait for your code to actually run that function
3. Receive the numbers
4. Generate a human-readable insight as structured JSON

**Still no UI, still no HTTP API.** Just a Python script that proves the pattern works end to end.

This phase is the most important one. Internalize it.

---

## The Mental Model (Read This First)

Gemini cannot execute code. It cannot touch your database. It can only:
- Read text
- Generate text
- *Indicate which function it thinks you should call* (and with what arguments)

Your code is the one that actually runs the function. Then you send the result back to Gemini, and it reasons over the data.

It's a back-and-forth conversation between **your code** and **Gemini**, with the database living entirely on your side.

```
┌────────────┐                     ┌─────────────┐
│            │  Round 1: prompt    │             │
│            │ ──────────────────► │             │
│            │                     │             │
│            │  Round 1: "call     │             │
│   YOUR     │  get_latest_run()"  │             │
│   CODE     │ ◄────────────────── │   GEMINI    │
│            │                     │             │
│            │  [you run the fn]   │             │
│            │   against the DB    │             │
│            │                     │             │
│            │  Round 2: results   │             │
│            │ ──────────────────► │             │
│            │                     │             │
│            │  Round 2: insight   │             │
│            │ ◄────────────────── │             │
└────────────┘                     └─────────────┘
```

Two rounds of conversation per user question. Got it? Good.

---

## What Claude Code Will Build

```
querymind/
├── backend/
│   ├── tool_schemas.py        # NEW — describes your tools to Gemini
│   ├── gemini_client.py       # NEW — the two-round conversation loop
│   ├── test_gemini.py         # NEW — standalone script to verify it works
│   └── requirements.txt       # UPDATED — add google-genai
```

Three new files + one updated file. No FastAPI yet, no UI.

---

## File 1: Updated `backend/requirements.txt`

Add `google-genai`:

```
asyncpg==0.30.0
python-dotenv==1.0.1
google-genai==0.3.0
```

---

## File 2: `backend/tool_schemas.py` — Describing Tools to Gemini

Gemini doesn't read your Python code. It reads **descriptions** of what your functions do. These descriptions are the *only* thing it uses to decide which function to call.

This is the single most important file to get right. **Bad descriptions = wrong tool called = wrong answer.**

```python
"""
Tool schemas describe each backend function to Gemini in a structured way.

Gemini reads:
- name: which function this represents
- description: WHAT this function does and WHEN to use it
- parameters: what inputs it needs (using JSON Schema)

Gemini does NOT see the actual Python code. The description text is the only
signal it uses to decide whether to call this function for a given user message.

GUIDELINE: descriptions should answer "when should the LLM use this?", not just
"what does this do?". Verbs like 'Use when the user...' are very effective.
"""

TOOL_DECLARATIONS = [
    {
        "name": "get_latest_run_metrics",
        "description": (
            "Fetches throughput, latency percentiles (P50/P95/P99), CPU, memory, "
            "and error rate for the MOST RECENTLY EXECUTED benchmark run. "
            "Use when the user asks about their latest, most recent, or last benchmark, "
            "or asks for a summary without specifying a run ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_run_metrics",
        "description": (
            "Fetches metrics for a SPECIFIC benchmark run by its run ID "
            "(e.g. R001, R005, R010). "
            "Use when the user explicitly mentions a run ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "run_id": {
                    "type": "string",
                    "description": "The run ID to fetch, e.g. R001"
                }
            },
            "required": ["run_id"],
        },
    },
    {
        "name": "get_all_runs",
        "description": (
            "Returns a list of all available benchmark runs with their IDs, names, "
            "workload types, and execution timestamps (no metrics, just metadata). "
            "Use when the user wants to see all runs, list available benchmarks, "
            "or doesn't reference any specific run ID."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_ab_comparison",
        "description": (
            "Compares two benchmark runs and returns their metrics side by side "
            "with computed percentage deltas. "
            "Use when the user asks to compare two specific runs, check for "
            "regressions between two runs, or asks which of two runs performed better."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "run_a_id": {"type": "string", "description": "First run ID"},
                "run_b_id": {"type": "string", "description": "Second run ID"},
            },
            "required": ["run_a_id", "run_b_id"],
        },
    },
    {
        "name": "get_trend_analysis",
        "description": (
            "Returns the last N benchmark runs ordered by time (newest first). "
            "Use when the user asks about trends, patterns over time, whether "
            "performance is improving or degrading, or about the last N runs."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Number of recent runs to include. Default 5."
                }
            },
            "required": [],
        },
    },
]
```

### Why descriptions matter so much

Imagine you only had one-word names: `latest`, `specific`, `list`, `compare`, `trend`. Gemini would have to guess. With descriptions like *"Use when the user asks about their latest, most recent, or last benchmark"*, Gemini has explicit, unambiguous trigger words to match against the user's message.

**Rule of thumb**: a good tool description tells the LLM *when* to use it, not just *what* it does.

---

## File 3: `backend/gemini_client.py` — The Two-Round Loop

This is the heart of the project. Read every line carefully.

```python
"""
Gemini Tool Calling Loop — the core of QueryMind.

This file implements the two-round conversation:

  Round 1:  Send user message + tool definitions  →  Gemini decides what to call
  Round 2:  Run the tool, send result back        →  Gemini generates final insight

The LLM never touches the database. It only reasons over data we hand it.
"""

import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

from tool_schemas import TOOL_DECLARATIONS
from tools import (
    get_latest_run_metrics,
    get_run_metrics,
    get_all_runs,
    get_ab_comparison,
    get_trend_analysis,
)

load_dotenv()

# Create the Gemini client once — it's thread-safe and meant to be reused.
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


# ─────────────────────────────────────────────────────────────────────────────
# System Prompt
# ─────────────────────────────────────────────────────────────────────────────
# This tells Gemini:
#   1. What its role is (DB performance analyst)
#   2. What patterns to look for in the data
#   3. What format to respond in (strict JSON for the UI to consume)
#
# The forced JSON shape is critical — our future React UI will render charts
# based on `chart_type` and `chart_data`. Free-form prose can't drive a chart.
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a database performance analysis assistant. You help engineers understand benchmark results by analyzing metrics like throughput (TPS), latency percentiles (P50/P95/P99), CPU usage, memory usage, and error rates.

When you receive data:
- Highlight anything concerning (P99 significantly higher than P95 suggests tail latency spikes)
- Flag CPU above 75% as approaching saturation
- Flag error rates above 0.01 (1%) as significant
- Be specific with numbers, not vague
- Keep insights concise and actionable (2-4 sentences)

You MUST respond ONLY with a raw JSON object in this exact shape — no markdown fences, no prose outside the JSON:
{
  "insight": "your natural language analysis here",
  "chart_type": "bar" | "line" | "none",
  "chart_data": [ { "name": "label", "value": number }, ... ]
}

Rules for chart_data:
- Single run summary: chart_type="bar", chart_data shows P50/P95/P99 latency as three bars
- A/B comparison: chart_type="bar", chart_data shows throughput for both runs side by side
- Trend analysis: chart_type="line", chart_data shows throughput per run in chronological order
- Listing runs or no numeric data: chart_type="none", chart_data=[]
"""


# ─────────────────────────────────────────────────────────────────────────────
# Tool Dispatch Table
# ─────────────────────────────────────────────────────────────────────────────
# Maps Gemini's tool name → the actual Python function that runs it.
# Each entry is an async lambda that takes the args dict Gemini provides.
#
# This is where Gemini's "decision" becomes a real function call.
# ─────────────────────────────────────────────────────────────────────────────

TOOL_DISPATCH = {
    "get_latest_run_metrics": lambda args: get_latest_run_metrics(),
    "get_run_metrics": lambda args: get_run_metrics(args["run_id"]),
    "get_all_runs": lambda args: get_all_runs(),
    "get_ab_comparison": lambda args: get_ab_comparison(args["run_a_id"], args["run_b_id"]),
    "get_trend_analysis": lambda args: get_trend_analysis(args.get("limit", 5)),
}


# Build the Tool object Gemini expects — wraps all our function declarations.
TOOLS = [types.Tool(function_declarations=TOOL_DECLARATIONS)]


# ─────────────────────────────────────────────────────────────────────────────
# The Main Conversation Function
# ─────────────────────────────────────────────────────────────────────────────

async def run_conversation(user_message: str) -> dict:
    """
    Two-round tool calling loop.

    Round 1: Send user message + tool definitions. Gemini may:
             (a) Respond directly without a tool (rare, e.g. "what can you do?")
             (b) Ask us to call a tool (the common case)

    Round 2: We execute the tool, send the result back. Gemini produces the
             final insight as JSON.
    """

    # ── Round 1 ──────────────────────────────────────────────────────────────
    contents = [
        types.Content(
            role="user",
            parts=[types.Part(text=user_message)],
        )
    ]

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=TOOLS,
        ),
    )

    # Look through the response for a function call
    function_call = None
    for part in response.candidates[0].content.parts:
        if part.function_call:
            function_call = part.function_call
            break

    # If Gemini answered without calling a tool, just parse and return
    if function_call is None:
        return _parse_json_response(response.text)

    # ── Execute the tool ─────────────────────────────────────────────────────
    fn_name = function_call.name
    fn_args = dict(function_call.args) if function_call.args else {}

    print(f"\n[Tool Call] Gemini wants to call: {fn_name}({fn_args})")

    if fn_name not in TOOL_DISPATCH:
        return {
            "insight": f"Error: Gemini requested unknown tool '{fn_name}'",
            "chart_type": "none",
            "chart_data": [],
        }

    tool_result = await TOOL_DISPATCH[fn_name](fn_args)

    print(f"[Tool Result] {json.dumps(tool_result, indent=2, default=str)[:300]}...")

    # ── Round 2 ──────────────────────────────────────────────────────────────
    # We need to send Gemini's turn AND our function response back, so it
    # knows the context of the conversation.
    contents.append(response.candidates[0].content)
    contents.append(
        types.Content(
            role="user",
            parts=[
                types.Part(
                    function_response=types.FunctionResponse(
                        name=fn_name,
                        response={"result": tool_result},
                    )
                )
            ],
        )
    )

    final_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=TOOLS,
        ),
    )

    return _parse_json_response(final_response.text)


# ─────────────────────────────────────────────────────────────────────────────
# JSON Parsing Helper
# ─────────────────────────────────────────────────────────────────────────────
# Gemini SOMETIMES wraps JSON in markdown fences (```json ... ```) despite the
# system prompt telling it not to. This helper strips fences before parsing
# so the program is robust to that quirk.
# ─────────────────────────────────────────────────────────────────────────────

def _parse_json_response(text: str) -> dict:
    cleaned = text.strip()

    # Strip ```json or ``` fences if present
    if cleaned.startswith("```"):
        # Drop first fence line
        cleaned = cleaned.split("```", 1)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        # Drop closing fence
        if "```" in cleaned:
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # If Gemini refused to return JSON, wrap whatever it said
        return {
            "insight": text,
            "chart_type": "none",
            "chart_data": [],
        }
```

---

## File 4: `backend/test_gemini.py` — Verifying the Pattern Works

This script runs through real questions and prints what Gemini decides + the final insight.

```python
"""
test_gemini.py — End-to-end test of the Gemini tool calling loop.

Run this AFTER test_tools.py passes. It exercises the full pattern:
  user message → Gemini → tool call → DB → Gemini → insight
"""

import asyncio
import json
from database import init_pool, close_pool
from gemini_client import run_conversation


TEST_QUERIES = [
    "Tell me the summary of my last benchmark",
    "Show me metrics for run R004",
    "Compare run R007 and R008",
    "Is performance improving over the last 5 runs?",
    "List all my benchmark runs",
]


def print_section(title: str):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


async def main():
    await init_pool()

    try:
        for query in TEST_QUERIES:
            print_section(f'USER: "{query}"')
            result = await run_conversation(query)

            print("\n[Final Insight]")
            print(json.dumps(result, indent=2))

            # Soft assertions — print warnings instead of failing
            if "insight" not in result:
                print("⚠ Response missing 'insight' field")
            if "chart_type" not in result:
                print("⚠ Response missing 'chart_type' field")

        print_section("DONE — review the insights above for quality")

    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step-by-Step Instructions for Claude Code

Hand this file to Claude Code with the prompt:

```
Please read PHASE_3.md and build Phase 3 of the QueryMind project.

Create/update these files in this order:
1. Update backend/requirements.txt to add google-genai
2. Create backend/tool_schemas.py
3. Create backend/gemini_client.py
4. Create backend/test_gemini.py

Use the exact code from the spec.

After all files are created, stop. I will install the new dependency and 
run test_gemini.py myself.
```

---

## How to Run It (Your Step)

### 1. Add your Gemini API key to `.env`
```
GEMINI_API_KEY=your_actual_key_here
DATABASE_URL=postgresql://postgres:root@localhost:5432/querymind
```

### 2. Install the new dependency
```bash
cd backend
pip install -r requirements.txt
```

### 3. Run the test
```bash
python test_gemini.py
```

### Expected output (5 sections, one per query)

Each section should print:
1. The user's question
2. `[Tool Call] Gemini wants to call: <function>(<args>)`
3. `[Tool Result] <truncated DB response>`
4. The final insight JSON

For "Tell me the summary of my last benchmark", you should see Gemini call `get_latest_run_metrics`, then return something roughly like:

```json
{
  "insight": "Your latest run R010 shows healthy throughput at ~5000 TPS with P99 latency around 56ms. CPU at 62% is comfortably below saturation. Overall, performance is solid.",
  "chart_type": "bar",
  "chart_data": [
    {"name": "P50", "value": 10},
    {"name": "P95", "value": 44},
    {"name": "P99", "value": 56}
  ]
}
```

The exact wording will vary — that's expected, it's an LLM. What matters is that **the right tool got called** and **the JSON shape is correct**.

---

## What You Should Understand After This Phase

These are THE concepts to internalize:

### 1. Gemini cannot execute code
It can only generate text. When you see "function_call" in its response, that's still just text saying "I think you should call this function". Your code is the one that actually runs it. This is the same for Claude, OpenAI, etc.

### 2. Tool descriptions are the entire decision-making input
Gemini doesn't see your Python code. It only sees the strings in `tool_schemas.py`. If a tool gets called for the wrong question, **the description is wrong**, not Gemini. Iterate on descriptions, not on prompt engineering.

### 3. The two-round pattern is universal
Round 1: prompt + tools → tool call. Round 2: tool result → final answer. This is the same pattern at OpenAI, Anthropic, and Google. Once you understand it for Gemini, you understand it everywhere.

### 4. JSON-forced output is how you bridge LLM → structured UI
Without forcing JSON, you'd get prose like "Your throughput was great!" and have no way to render a chart. By making Gemini output `{insight, chart_type, chart_data}`, your frontend code stays simple: read the fields, render the chart.

### 5. System prompt vs tool descriptions
- **System prompt**: what the assistant *is*, how to *behave*, what *format* to output
- **Tool descriptions**: *when* to use each tool

They're different concerns. Keep them separated.

### 6. Why "function calling" beats RAG here (revisited)
You now have proof. The data Gemini gets back is exact numbers — `4823.0` TPS, `134.2` ms P99. No vector similarity, no embedding noise. The LLM reasons over precise values. That's why this pattern beats RAG for numerical data.

---

## Common Things to Watch For

While running `test_gemini.py`, watch for these issues:

| Symptom | Likely Cause |
|---|---|
| Gemini calls wrong tool | Tool description too vague — iterate on it |
| `JSONDecodeError` silenced into "insight" field | Gemini didn't follow JSON format — system prompt may need to be sterner |
| `function_call.args` is missing keys | Tool schema's `required` field is wrong, or Gemini didn't extract the run ID |
| "Run not found" in tool result | Gemini hallucinated a run ID — usually fine, the insight should acknowledge it |
| 403 / API key error | Wrong Gemini key, or quota exceeded |
| `model not found` | Try `gemini-1.5-flash` if `gemini-2.5-flash` isn't available in your region |

---

## Done?

Before moving on, confirm:
- [ ] All 4 files exist
- [ ] `pip install` completed
- [ ] `python test_gemini.py` ran without crashes
- [ ] For each of the 5 test queries, Gemini called a reasonable tool
- [ ] The final insights are coherent and reference real numbers from your DB
- [ ] You can explain the 6 conceptual points above in your own words

When all that's true, come back and I'll send **Phase 4: FastAPI Backend** — where we wrap this in an HTTP endpoint so a frontend can talk to it.