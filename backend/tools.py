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
