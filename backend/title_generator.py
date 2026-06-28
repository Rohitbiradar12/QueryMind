"""
title_generator.py — Auto-generate short chat titles from the first user message.

Gemini gets a strict 5-word ceiling and a single example. We use the same
client as gemini_client.py but with a much simpler prompt — no tools, no JSON.
"""

import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

TITLE_SYSTEM_PROMPT = """Generate a 2-5 word title for a chat based on the user's first message.

Rules:
- Maximum 5 words
- No quotes, no punctuation at the end
- Be specific about the topic (mention run IDs, metric names if relevant)
- Use title case sparingly — sentence case is fine

Examples:
User: "Tell me about my last benchmark" → Latest benchmark summary
User: "Compare runs R007 and R008" → R007 vs R008 comparison
User: "Why is P99 so high in R004?" → R004 tail latency
User: "Show me throughput trends" → Throughput trends

Return ONLY the title text. No explanations, no markdown.
"""


async def generate_title(first_message: str) -> str:
    """Calls Gemini to produce a short chat title. Falls back if it fails."""
    try:
        response = _client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents=[types.Content(role="user", parts=[types.Part(text=first_message)])],
            config=types.GenerateContentConfig(
                system_instruction=TITLE_SYSTEM_PROMPT,
            ),
        )
        title = response.text.strip().strip('"').strip("'")
        # Hard cap to be safe
        if len(title) > 80:
            title = title[:77] + "..."
        return title or "New chat"
    except Exception as e:
        print(f"[title_generator] Failed to generate title: {e}")
        return "New chat"
