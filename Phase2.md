# Phase 2 — Query Functions (Tools)

## Goal of This Phase

Build the **read-only Python functions** that fetch benchmark data from the database. These are the functions Gemini will eventually call in Phase 3, but for now we're just building and testing them directly — no AI yet.

By the end of this phase, you'll have:
- A working database connection pool
- 5 query functions that return clean Python dicts
- A small test script to verify each function works against your real DB

**No AI integration yet** — we're proving the data layer works first.

---

## Why "Read-Only"?

Every function in this phase only does `SELECT`. No INSERT, UPDATE, or DELETE. This is intentional and matters at AWS too:

- The LLM should never be able to mutate data through these tools
- If a function only reads, the worst-case bug is wrong output — never data loss
- It's the same principle as giving an intern read-only DB credentials

This is a **non-negotiable design rule** for the AWS PAS version. Practice it here.

---

## What Claude Code Will Build

```
querymind/
├── backend/
│   ├── database.py          # asyncpg connection pool
│   ├── tools.py             # 5 query functions
│   ├── test_tools.py        # standalone script to test the functions
│   └── requirements.txt     # just the deps we need for this phase
├── .env                     # already exists from before
└── .env.example
```

5 files. Nothing AI-related yet.

---

## File 1: `backend/requirements.txt`

For this phase, only these dependencies:

```
asyncpg==0.30.0
python-dotenv==1.0.1
```

We'll add FastAPI and Gemini in later phases.

---

## File 2: `backend/database.py`

A simple async connection pool. asyncpg uses a pool so we don't open/close a connection on every query (expensive).

```python
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

_pool: asyncpg.Pool | None = None


async def init_pool() -> asyncpg.Pool:
    """Create the connection pool. Call once on startup."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            DATABASE_URL,
            min_size=1,
            max_size=5,
        )
    return _pool


async def close_pool() -> None:
    """Close the pool. Call on shutdown."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


async def get_pool() -> asyncpg.Pool:
    """Get the current pool. Raises if not initialized."""
    if _pool is None:
        raise RuntimeError("Pool not initialized. Call init_pool() first.")
    return _pool
```

### Why a pool?
Opening a new DB connection takes ~50-100ms. With a pool, you open 1-5 connections upfront and reuse them. Every query reuses an existing connection. This matters when you have a chat UI making many queries.

---

## File 3: `backend/tools.py`

The 5 query functions. Each returns a plain Python dict (or list of dicts) so it can be serialized to JSON later when we send it back to Gemini.

```python
from datetime import datetime
from database import get_pool


# Helper to convert asyncpg Record → plain dict
def _record_to_dict(record) -> dict:
    if record is None:
        return None
    d = dict(record)
    # Convert datetime to ISO string for JSON serialization
    for key, value in d.items():
        if isinstance(value, datetime):
            d[key] = value.isoformat()
    return d


async def get_latest_run_metrics() -> dict:
    """Returns metrics for the most recently executed benchmark run."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                r.run_id, r.run_name, r.workload, r.executed_at,
                m.throughput_tps, m.p50_ms, m.p95_ms, m.p99_ms,
                m.cpu_pct, m.memory_pct, m.error_rate
            FROM benchmark_runs r
            JOIN benchmark_metrics m ON r.run_id = m.run_id
            ORDER BY r.executed_at DESC
            LIMIT 1
        """)
        return _record_to_dict(row)


async def get_run_metrics(run_id: str) -> dict:
    """Returns metrics for a specific run by ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("""
            SELECT
                r.run_id, r.run_name, r.workload, r.executed_at,
                m.throughput_tps, m.p50_ms, m.p95_ms, m.p99_ms,
                m.cpu_pct, m.memory_pct, m.error_rate
            FROM benchmark_runs r
            JOIN benchmark_metrics m ON r.run_id = m.run_id
            WHERE r.run_id = $1
        """, run_id)
        if row is None:
            return {"error": f"Run {run_id} not found"}
        return _record_to_dict(row)


async def get_all_runs() -> list[dict]:
    """Returns metadata for all runs (no metrics)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT run_id, run_name, workload, executed_at
            FROM benchmark_runs
            ORDER BY executed_at DESC
        """)
        return [_record_to_dict(row) for row in rows]


async def get_ab_comparison(run_a_id: str, run_b_id: str) -> dict:
    """Compares two runs with computed percentage deltas."""
    run_a = await get_run_metrics(run_a_id)
    run_b = await get_run_metrics(run_b_id)

    if "error" in run_a:
        return {"error": f"Run A ({run_a_id}) not found"}
    if "error" in run_b:
        return {"error": f"Run B ({run_b_id}) not found"}

    def pct_change(a: float, b: float) -> float:
        if a == 0:
            return 0.0
        return round(((b - a) / a) * 100, 2)

    deltas = {
        "throughput_tps_change_pct": pct_change(run_a["throughput_tps"], run_b["throughput_tps"]),
        "p50_ms_change_pct": pct_change(run_a["p50_ms"], run_b["p50_ms"]),
        "p95_ms_change_pct": pct_change(run_a["p95_ms"], run_b["p95_ms"]),
        "p99_ms_change_pct": pct_change(run_a["p99_ms"], run_b["p99_ms"]),
        "cpu_pct_change": round(run_b["cpu_pct"] - run_a["cpu_pct"], 2),
    }

    return {
        "run_a": run_a,
        "run_b": run_b,
        "deltas": deltas,
    }


async def get_trend_analysis(limit: int = 5) -> dict:
    """Returns the last N runs ordered by time (newest first)."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT
                r.run_id, r.run_name, r.workload, r.executed_at,
                m.throughput_tps, m.p50_ms, m.p95_ms, m.p99_ms,
                m.cpu_pct, m.memory_pct, m.error_rate
            FROM benchmark_runs r
            JOIN benchmark_metrics m ON r.run_id = m.run_id
            ORDER BY r.executed_at DESC
            LIMIT $1
        """, limit)
        return {
            "runs": [_record_to_dict(row) for row in rows],
            "count": len(rows),
        }
```

### Why each function returns a dict (not a custom class)?
Because in Phase 3, we'll send these results back to Gemini as JSON. Dicts → JSON is one step (`json.dumps`). A custom class needs extra serialization logic. Keep it simple.

### Why parameterized queries (`$1`) and not f-strings?
Even though this is a POC, get the habit right: **never** interpolate user input into SQL. asyncpg's `$1`, `$2` placeholders prevent SQL injection. Even if Gemini misbehaves and passes weird input, asyncpg treats it as data, not SQL.

---

## File 4: `backend/test_tools.py`

A standalone script to verify everything works. **This is critical** — you cannot move to Phase 3 until all 5 functions return correct data.

```python
import asyncio
import json
from database import init_pool, close_pool
from tools import (
    get_latest_run_metrics,
    get_run_metrics,
    get_all_runs,
    get_ab_comparison,
    get_trend_analysis,
)


def print_section(title: str):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


async def main():
    await init_pool()

    try:
        print_section("1. get_latest_run_metrics()")
        result = await get_latest_run_metrics()
        print(json.dumps(result, indent=2))
        assert result["run_id"] == "R010", f"Expected R010, got {result['run_id']}"
        print("✓ Latest run is R010")

        print_section("2. get_run_metrics('R004')  [tail latency case]")
        result = await get_run_metrics("R004")
        print(json.dumps(result, indent=2))
        assert result["p99_ms"] > 200, f"Expected P99 > 200, got {result['p99_ms']}"
        print("✓ R004 has high P99 (tail latency)")

        print_section("3. get_run_metrics('RXYZ')  [should return error]")
        result = await get_run_metrics("RXYZ")
        print(json.dumps(result, indent=2))
        assert "error" in result
        print("✓ Missing run returns error dict")

        print_section("4. get_all_runs()")
        result = await get_all_runs()
        print(f"Total runs: {len(result)}")
        print(json.dumps(result[:3], indent=2))
        assert len(result) == 10, f"Expected 10 runs, got {len(result)}"
        print("✓ Returned 10 runs")

        print_section("5. get_ab_comparison('R006', 'R007')")
        result = await get_ab_comparison("R006", "R007")
        print(json.dumps(result, indent=2))
        assert result["deltas"]["throughput_tps_change_pct"] > 0
        print("✓ R007 shows positive throughput delta vs R006")

        print_section("6. get_ab_comparison('R007', 'R008')  [regression case]")
        result = await get_ab_comparison("R007", "R008")
        print(json.dumps(result, indent=2))
        assert result["deltas"]["throughput_tps_change_pct"] < -20
        print("✓ R008 shows clear regression vs R007")

        print_section("7. get_trend_analysis(limit=5)")
        result = await get_trend_analysis(5)
        print(json.dumps(result, indent=2))
        assert result["count"] == 5
        print("✓ Returned exactly 5 runs")

        print("\n" + "=" * 60)
        print("  ALL TESTS PASSED ✓")
        print("=" * 60)

    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step-by-Step Instructions for Claude Code

Hand `PHASE_2.md` to Claude Code with this prompt:

```
Please read PHASE_2.md and build Phase 2 of the QueryMind project.

Create these 4 files in this order:
1. backend/requirements.txt
2. backend/database.py
3. backend/tools.py
4. backend/test_tools.py

Use the exact code from the spec.

After all files are created, stop. I will install dependencies and 
run test_tools.py myself to verify everything works.
```

---

## How to Run It (Your Step)

After Claude Code creates the files:

### 1. Install dependencies
```bash
cd backend
pip install -r requirements.txt
```

### 2. Make sure `.env` is in the project root
It should look like this (you already have it from earlier):
```
GEMINI_API_KEY=your_key_here
DATABASE_URL=postgresql://postgres:root@localhost:5432/querymind
```

> The `GEMINI_API_KEY` doesn't matter yet — we're not using AI this phase.

### 3. Run the test
```bash
cd backend
python test_tools.py
```

### Expected output
You should see 7 sections of test output ending with:
```
============================================================
  ALL TESTS PASSED ✓
============================================================
```

If anything fails:
- "Pool not initialized" → check `.env` path and DATABASE_URL value
- "could not translate host name" → Postgres isn't running
- "password authentication failed" → password mismatch
- "relation does not exist" → seed.sql wasn't run, or ran on the wrong DB
- Assertion error → seed data doesn't match what Phase 1 specified

---

## What You Should Understand After This Phase

Before moving on, make sure you can answer these:

### 1. Why a connection pool instead of opening connections per query?
Opening a Postgres connection takes ~50-100ms (TCP handshake, auth, SSL). Inside a chat app that issues multiple queries per user message, that overhead compounds fast. A pool keeps 1-5 connections warm and hands them out on demand — every query reuses an existing connection.

### 2. Why are the functions `async`?
asyncpg is built on Python's asyncio. Async lets the server handle multiple incoming requests concurrently — while one request is waiting on the DB, another can be processed. FastAPI (which we'll add in Phase 4) is async-native and will call these functions directly with `await`.

### 3. Why do these functions return dicts, not custom classes?
In Phase 3, we send these results back to Gemini as JSON. `dict → json.dumps()` is one line. A class would need a custom serializer. The whole point of the tool result is to be cleanly serializable.

### 4. Why parameterized queries (`$1`) instead of f-strings?
SQL injection prevention. With f-strings, a value like `R001'; DROP TABLE benchmark_runs;--` would execute as SQL. With `$1`, asyncpg sends the value separately from the query string — Postgres treats it as data, never code. Even though Gemini is the one filling these in (not a user directly), get the habit right.

### 5. Where does the "tool" concept actually appear here?
Nowhere yet. These are just Python functions. What makes them "tools" comes in Phase 3, when we *describe* them to Gemini in a structured schema and Gemini decides which one to call. The functions themselves are just data accessors.

---

## Done?

Before moving on, confirm:
- [ ] All 4 files exist
- [ ] `pip install -r requirements.txt` ran without errors
- [ ] `python test_tools.py` printed `ALL TESTS PASSED ✓`
- [ ] You can explain the 5 conceptual questions above

When all that's true, come back and I'll send **Phase 3: Gemini Tool Calling** — this is the most important phase. It's where the LLM pattern actually clicks.