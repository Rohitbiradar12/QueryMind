# Phase 1 — Database + Seed Data

## Goal of This Phase

Set up the PostgreSQL schema and load realistic fake benchmark data. By the end of this phase, you'll have a `querymind` database with two tables and 10 benchmark runs that we can query.

**No backend or AI code yet** — just the data layer.

---

## What You Already Have

- PostgreSQL installed and running on `localhost:5432`
- pgAdmin 4 connected to the server
- An empty database named `querymind`
- Credentials: `postgres` / `root`

---

## What Claude Code Will Build

Just **one file**:

```
querymind/
└── db/
    └── seed.sql
```

That's it for this phase. One SQL file.

---

## Schema Specification

### Table 1: `benchmark_runs`
Stores metadata about each benchmark test run.

| Column | Type | Notes |
|---|---|---|
| `run_id` | VARCHAR(10) | Primary key. Format: `R001`, `R002`, ..., `R010` |
| `run_name` | VARCHAR(100) | Descriptive name e.g. `baseline-mixed-load` |
| `workload` | VARCHAR(50) | One of: `read-heavy`, `write-heavy`, `mixed` |
| `executed_at` | TIMESTAMP | When the run was executed |

### Table 2: `benchmark_metrics`
Stores the actual performance metrics. One row per run.

| Column | Type | Notes |
|---|---|---|
| `id` | SERIAL | Primary key, auto-increment |
| `run_id` | VARCHAR(10) | Foreign key → `benchmark_runs(run_id)` |
| `throughput_tps` | FLOAT | Transactions per second |
| `p50_ms` | FLOAT | Median latency in milliseconds |
| `p95_ms` | FLOAT | 95th percentile latency |
| `p99_ms` | FLOAT | 99th percentile latency (tail latency) |
| `cpu_pct` | FLOAT | CPU usage percentage (0-100) |
| `memory_pct` | FLOAT | Memory usage percentage (0-100) |
| `error_rate` | FLOAT | Error rate from 0.0 to 1.0 |

---

## Seed Data Requirements

Insert exactly **10 runs** (R001 through R010) with these specific characteristics. Pick `executed_at` timestamps spread across the last 30 days, with R001 being the oldest and R010 the most recent.

### R001 — baseline healthy
- workload: `mixed`
- throughput_tps: ~4500
- p50_ms: ~10, p95_ms: ~45, p99_ms: ~55
- cpu_pct: ~50, memory_pct: ~55
- error_rate: ~0.001

### R002 — baseline healthy
- workload: `read-heavy`
- throughput_tps: ~5200
- p50_ms: ~8, p95_ms: ~40, p99_ms: ~50
- cpu_pct: ~45, memory_pct: ~50
- error_rate: ~0.0005

### R003 — baseline healthy
- workload: `mixed`
- throughput_tps: ~4700
- p50_ms: ~11, p95_ms: ~46, p99_ms: ~58
- cpu_pct: ~55, memory_pct: ~58
- error_rate: ~0.001

### R004 — TAIL LATENCY ISSUE
- workload: `mixed`
- throughput_tps: ~4600
- p50_ms: ~12, p95_ms: ~60, **p99_ms: 250** (huge tail latency spike)
- cpu_pct: ~58, memory_pct: ~60
- error_rate: ~0.002

### R005 — CPU SATURATION
- workload: `write-heavy`
- throughput_tps: ~4800 (plateaued)
- p50_ms: ~15, p95_ms: ~55, p99_ms: ~95
- **cpu_pct: 88**, memory_pct: ~70
- error_rate: ~0.003

### R006 — pre-optimization (A in A/B)
- workload: `read-heavy`
- throughput_tps: ~4000
- p50_ms: ~14, p95_ms: ~50, p99_ms: ~65
- cpu_pct: ~60, memory_pct: ~58
- error_rate: ~0.002

### R007 — post-optimization (B in A/B, +20% throughput)
- workload: `read-heavy`
- throughput_tps: ~4800 (20% better than R006)
- p50_ms: ~10, p95_ms: ~42, p99_ms: ~52
- cpu_pct: ~52, memory_pct: ~55
- error_rate: ~0.001

### R008 — REGRESSION vs R007 (30% throughput drop)
- workload: `read-heavy`
- throughput_tps: ~3360 (30% worse than R007)
- p50_ms: ~18, p95_ms: ~70, p99_ms: ~110
- cpu_pct: ~72, memory_pct: ~68
- error_rate: ~0.008

### R009 — recovery, trending up
- workload: `mixed`
- throughput_tps: ~4400
- p50_ms: ~12, p95_ms: ~48, p99_ms: ~62
- cpu_pct: ~58, memory_pct: ~60
- error_rate: ~0.002

### R010 — latest, healthy
- workload: `mixed`
- throughput_tps: ~5000
- p50_ms: ~10, p95_ms: ~44, p99_ms: ~56
- cpu_pct: ~62, memory_pct: ~60
- error_rate: ~0.001

### `run_name` suggestions
Use descriptive names so they look realistic:
- `baseline-mixed-may`
- `read-perf-baseline`
- `peak-load-test`
- `tail-latency-investigation`
- `write-stress-test`
- `pre-index-optimization`
- `post-index-optimization`
- `regression-build-447`
- `recovery-validation`
- `stress-test-june`

---

## Step-by-Step Instructions for Claude Code

When you hand this file to Claude Code, give it this exact prompt:

```
Please read PHASE_1.md and create db/seed.sql.

The file should:
1. Drop existing tables if they exist (so it's safe to re-run)
2. Create both tables with the exact schema specified
3. Insert all 10 benchmark runs into benchmark_runs
4. Insert one corresponding metrics row per run into benchmark_metrics
5. Include comments above each run explaining what scenario it represents

Do not create any other files. After creating seed.sql, stop and wait for me 
to run it in pgAdmin before continuing.
```

---

## How to Run seed.sql (Your Step)

Once Claude Code creates `db/seed.sql`:

1. Open pgAdmin → expand server → Databases → right-click `querymind` → **Query Tool**
2. In the Query Tool, click the **Open File** icon (folder icon) at the top
3. Navigate to your `querymind/db/seed.sql` file and open it
4. Click **Execute (▶)** or press **F5**
5. You should see a success message at the bottom

---

## Verification (Important — Do This Before Moving On)

Run these queries in pgAdmin's Query Tool to confirm everything loaded correctly:

```sql
-- Should return 10
SELECT COUNT(*) FROM benchmark_runs;

-- Should return 10
SELECT COUNT(*) FROM benchmark_metrics;

-- Should show all 10 runs ordered by time
SELECT * FROM benchmark_runs ORDER BY executed_at;

-- Should show R004 with a P99 around 250
SELECT run_id, p95_ms, p99_ms FROM benchmark_metrics WHERE run_id = 'R004';

-- Should show R005 with cpu_pct around 88
SELECT run_id, cpu_pct FROM benchmark_metrics WHERE run_id = 'R005';
```

If any of these return unexpected results, ask Claude Code to fix the seed file.

---

## What You Should Understand After This Phase

Before moving to Phase 2, make sure you can answer these:

1. **Why two tables instead of one?**
   - `benchmark_runs` holds metadata, `benchmark_metrics` holds measurements
   - This is normalized — same pattern PAS likely uses internally
   - One run could potentially have multiple metric snapshots over time (we're using one for simplicity, but the schema allows growth)

2. **Why the specific weird data values?**
   - R004's huge P99 simulates a real-world tail latency issue
   - R005's CPU at 88% simulates approaching saturation
   - R007 → R008 simulates a real regression you'd want the AI to flag
   - The variation is what makes the LLM's insights *interesting* — if everything looked identical, there'd be nothing to analyze

3. **Why timestamps spread across 30 days?**
   - So queries like "is performance improving over time?" actually have a time dimension to reason about
   - "Trend analysis" needs ordered-by-time data to detect patterns

---

## Done?

Once you've:
- [ ] Generated `seed.sql` via Claude Code
- [ ] Run it successfully in pgAdmin
- [ ] Verified all 5 queries above return expected results
- [ ] Understood the 3 conceptual questions

Come back and I'll give you **Phase 2: Query Functions (Tools)**.