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
