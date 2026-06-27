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
            "type": "OBJECT",
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
            "type": "OBJECT",
            "properties": {
                "run_id": {
                    "type": "STRING",
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
            "type": "OBJECT",
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
            "type": "OBJECT",
            "properties": {
                "run_a_id": {"type": "STRING", "description": "First run ID"},
                "run_b_id": {"type": "STRING", "description": "Second run ID"},
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
            "type": "OBJECT",
            "properties": {
                "limit": {
                    "type": "INTEGER",
                    "description": "Number of recent runs to include. Default 5."
                }
            },
            "required": [],
        },
    },
]
