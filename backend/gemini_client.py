"""
Gemini Tool Calling Loop — now with conversation history support.

The key change vs Phase 3: instead of a single user message, we accept a list
of prior messages. Gemini sees the full history and can answer follow-ups in
context ("how does it compare?" knows what "it" refers to).

Two-round pattern still applies — Gemini may request a tool, we run it, send
result back, get final JSON insight.
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

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

MODEL = "gemini-2.5-flash-lite"
# The lite model occasionally returns an empty candidate (0 parts, finish=STOP).
# We retry the generation a couple times before giving up gracefully. Kept low
# to stay gentle on the limited free-tier quota.
MAX_EMPTY_RETRIES = 2


SYSTEM_PROMPT = """You are a database performance analysis assistant. You help engineers understand benchmark results by analyzing metrics like throughput (TPS), latency percentiles (P50/P95/P99), CPU usage, memory usage, and error rates.

When you receive data:
- Highlight anything concerning (P99 significantly higher than P95 suggests tail latency spikes)
- Flag CPU above 75% as approaching saturation
- Flag error rates above 0.01 (1%) as significant
- Be specific with numbers, not vague
- Keep insights concise and actionable (2-4 sentences)
- When answering follow-up questions, reference what was discussed earlier when relevant

If the user asks about something outside benchmark performance analysis (general coding help, unrelated topics, math problems, etc.), do not refuse bluntly. Instead:
1. Briefly acknowledge what they asked
2. Explain that you're focused on benchmark performance insights
3. Suggest 1-2 specific benchmark questions they could ask instead (e.g. "Show me my latest benchmark" or "Compare R007 and R008")
4. Keep the tone warm and helpful, not robotic
Even for off-topic refusals, you MUST still respond in the required JSON format with chart_type="none" and chart_data=[].

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


TOOL_DISPATCH = {
    "get_latest_run_metrics": lambda args: get_latest_run_metrics(),
    "get_run_metrics": lambda args: get_run_metrics(args["run_id"]),
    "get_all_runs": lambda args: get_all_runs(),
    "get_ab_comparison": lambda args: get_ab_comparison(args["run_a_id"], args["run_b_id"]),
    "get_trend_analysis": lambda args: get_trend_analysis(args.get("limit", 5)),
}

TOOLS = [types.Tool(function_declarations=TOOL_DECLARATIONS)]


def _history_to_contents(history: list[dict]) -> list:
    """
    Convert our stored chat history into Gemini's Content format.

    Input shape:   [{"role": "user"|"assistant", "content": "..."}]
    Output shape:  list of types.Content

    Gemini uses "model" instead of "assistant" — we translate.
    """
    contents = []
    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append(
            types.Content(role=role, parts=[types.Part(text=msg["content"])])
        )
    return contents


def _safe_text(response) -> str | None:
    """Extract concatenated text from a response without raising.

    `response.text` raises if the candidate holds a function_call part and
    returns None when the candidate is empty (a known lite-model quirk).
    This walks the parts defensively and returns None if there's no text.
    """
    try:
        parts = response.candidates[0].content.parts or []
    except (AttributeError, IndexError, TypeError):
        return None
    texts = [p.text for p in parts if getattr(p, "text", None)]
    return "".join(texts) if texts else None


def _generate(contents):
    """Call the model with our system prompt + tools."""
    return client.models.generate_content(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=TOOLS,
        ),
    )


async def run_conversation(history: list[dict]) -> dict:
    """
    Run the tool-calling loop with full conversation history.

    `history` is the complete chat so far, INCLUDING the new user message
    as its last entry. Each entry is {"role": "user"|"assistant", "content": str}.

    Returns: {"insight": str, "chart_type": str, "chart_data": list}
    """

    contents = _history_to_contents(history)

    # ── Round 1 ──────────────────────────────────────────────────────────────
    response = _generate(contents)

    function_call = None
    for part in (response.candidates[0].content.parts or []):
        if part.function_call:
            function_call = part.function_call
            break

    if function_call is None:
        # No tool needed — Gemini answered directly. Retry if it came back empty.
        text = _safe_text(response)
        attempts = 0
        while not text and attempts < MAX_EMPTY_RETRIES:
            attempts += 1
            response = _generate(contents)
            for part in (response.candidates[0].content.parts or []):
                if part.function_call:
                    function_call = part.function_call
                    break
            if function_call is not None:
                break
            text = _safe_text(response)
        if function_call is None:
            return _parse_json_response(text)

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

    # The lite model sometimes returns an empty round-2 response; retry a few
    # times until we get text back, then parse it.
    final_text = None
    for _ in range(MAX_EMPTY_RETRIES):
        final_response = _generate(contents)
        final_text = _safe_text(final_response)
        if final_text:
            break

    return _parse_json_response(final_text)


def _parse_json_response(text: str | None) -> dict:
    if not text:
        return {
            "insight": (
                "I had trouble generating a response just now. "
                "Please try asking again."
            ),
            "chart_type": "none",
            "chart_data": [],
        }
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 1)[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        if "```" in cleaned:
            cleaned = cleaned.rsplit("```", 1)[0]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"insight": text, "chart_type": "none", "chart_data": []}
