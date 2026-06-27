-- ============================================================
-- QueryMind — Phase 1 Seed File
-- ============================================================
-- Creates the schema and loads 10 realistic benchmark runs.
-- Safe to re-run: drops existing tables first.
--
-- Run in pgAdmin Query Tool against the `querymind` database.
-- ============================================================

-- ------------------------------------------------------------
-- 1. Clean slate (drop in dependency order)
-- ------------------------------------------------------------
DROP TABLE IF EXISTS benchmark_metrics;
DROP TABLE IF EXISTS benchmark_runs;

-- ------------------------------------------------------------
-- 2. Schema
-- ------------------------------------------------------------

-- Metadata about each benchmark test run.
CREATE TABLE benchmark_runs (
    run_id      VARCHAR(10)  PRIMARY KEY,        -- R001 .. R010
    run_name    VARCHAR(100) NOT NULL,           -- descriptive name
    workload    VARCHAR(50)  NOT NULL,           -- read-heavy | write-heavy | mixed
    executed_at TIMESTAMP    NOT NULL            -- when the run was executed
);

-- Performance metrics. One row per run.
CREATE TABLE benchmark_metrics (
    id             SERIAL      PRIMARY KEY,
    run_id         VARCHAR(10) NOT NULL REFERENCES benchmark_runs(run_id),
    throughput_tps FLOAT       NOT NULL,         -- transactions per second
    p50_ms         FLOAT       NOT NULL,         -- median latency (ms)
    p95_ms         FLOAT       NOT NULL,         -- 95th percentile latency (ms)
    p99_ms         FLOAT       NOT NULL,         -- 99th percentile / tail latency (ms)
    cpu_pct        FLOAT       NOT NULL,         -- CPU usage % (0-100)
    memory_pct     FLOAT       NOT NULL,         -- memory usage % (0-100)
    error_rate     FLOAT       NOT NULL          -- error rate (0.0 - 1.0)
);

-- ------------------------------------------------------------
-- 3. Seed data — benchmark_runs
-- ------------------------------------------------------------
-- Timestamps spread across the last ~30 days (today is 2026-06-27),
-- R001 oldest -> R010 most recent.

-- R001 — baseline healthy (mixed)
INSERT INTO benchmark_runs (run_id, run_name, workload, executed_at) VALUES
('R001', 'baseline-mixed-may', 'mixed', '2026-05-29 09:15:00');

-- R002 — baseline healthy (read-heavy)
INSERT INTO benchmark_runs (run_id, run_name, workload, executed_at) VALUES
('R002', 'read-perf-baseline', 'read-heavy', '2026-06-01 10:30:00');

-- R003 — baseline healthy (mixed)
INSERT INTO benchmark_runs (run_id, run_name, workload, executed_at) VALUES
('R003', 'peak-load-test', 'mixed', '2026-06-04 14:00:00');

-- R004 — TAIL LATENCY ISSUE (p99 spikes to ~250ms)
INSERT INTO benchmark_runs (run_id, run_name, workload, executed_at) VALUES
('R004', 'tail-latency-investigation', 'mixed', '2026-06-07 11:45:00');

-- R005 — CPU SATURATION (cpu ~88%, throughput plateaued)
INSERT INTO benchmark_runs (run_id, run_name, workload, executed_at) VALUES
('R005', 'write-stress-test', 'write-heavy', '2026-06-10 16:20:00');

-- R006 — pre-optimization (A in A/B test)
INSERT INTO benchmark_runs (run_id, run_name, workload, executed_at) VALUES
('R006', 'pre-index-optimization', 'read-heavy', '2026-06-13 08:50:00');

-- R007 — post-optimization (B in A/B test, +20% throughput)
INSERT INTO benchmark_runs (run_id, run_name, workload, executed_at) VALUES
('R007', 'post-index-optimization', 'read-heavy', '2026-06-16 13:10:00');

-- R008 — REGRESSION vs R007 (30% throughput drop)
INSERT INTO benchmark_runs (run_id, run_name, workload, executed_at) VALUES
('R008', 'regression-build-447', 'read-heavy', '2026-06-19 15:35:00');

-- R009 — recovery, trending up
INSERT INTO benchmark_runs (run_id, run_name, workload, executed_at) VALUES
('R009', 'recovery-validation', 'mixed', '2026-06-23 10:05:00');

-- R010 — latest, healthy
INSERT INTO benchmark_runs (run_id, run_name, workload, executed_at) VALUES
('R010', 'stress-test-june', 'mixed', '2026-06-26 17:40:00');

-- ------------------------------------------------------------
-- 4. Seed data — benchmark_metrics (one row per run)
-- ------------------------------------------------------------

-- R001 — baseline healthy
INSERT INTO benchmark_metrics
    (run_id, throughput_tps, p50_ms, p95_ms, p99_ms, cpu_pct, memory_pct, error_rate) VALUES
('R001', 4500, 10, 45, 55, 50, 55, 0.001);

-- R002 — baseline healthy
INSERT INTO benchmark_metrics
    (run_id, throughput_tps, p50_ms, p95_ms, p99_ms, cpu_pct, memory_pct, error_rate) VALUES
('R002', 5200, 8, 40, 50, 45, 50, 0.0005);

-- R003 — baseline healthy
INSERT INTO benchmark_metrics
    (run_id, throughput_tps, p50_ms, p95_ms, p99_ms, cpu_pct, memory_pct, error_rate) VALUES
('R003', 4700, 11, 46, 58, 55, 58, 0.001);

-- R004 — TAIL LATENCY ISSUE: p99 spikes to 250ms while p50/p95 stay normal
INSERT INTO benchmark_metrics
    (run_id, throughput_tps, p50_ms, p95_ms, p99_ms, cpu_pct, memory_pct, error_rate) VALUES
('R004', 4600, 12, 60, 250, 58, 60, 0.002);

-- R005 — CPU SATURATION: cpu at 88%, throughput plateaued
INSERT INTO benchmark_metrics
    (run_id, throughput_tps, p50_ms, p95_ms, p99_ms, cpu_pct, memory_pct, error_rate) VALUES
('R005', 4800, 15, 55, 95, 88, 70, 0.003);

-- R006 — pre-optimization baseline (A)
INSERT INTO benchmark_metrics
    (run_id, throughput_tps, p50_ms, p95_ms, p99_ms, cpu_pct, memory_pct, error_rate) VALUES
('R006', 4000, 14, 50, 65, 60, 58, 0.002);

-- R007 — post-optimization (B): ~20% higher throughput than R006
INSERT INTO benchmark_metrics
    (run_id, throughput_tps, p50_ms, p95_ms, p99_ms, cpu_pct, memory_pct, error_rate) VALUES
('R007', 4800, 10, 42, 52, 52, 55, 0.001);

-- R008 — REGRESSION: ~30% throughput drop vs R007, latency & errors up
INSERT INTO benchmark_metrics
    (run_id, throughput_tps, p50_ms, p95_ms, p99_ms, cpu_pct, memory_pct, error_rate) VALUES
('R008', 3360, 18, 70, 110, 72, 68, 0.008);

-- R009 — recovery, trending back up
INSERT INTO benchmark_metrics
    (run_id, throughput_tps, p50_ms, p95_ms, p99_ms, cpu_pct, memory_pct, error_rate) VALUES
('R009', 4400, 12, 48, 62, 58, 60, 0.002);

-- R010 — latest, healthy
INSERT INTO benchmark_metrics
    (run_id, throughput_tps, p50_ms, p95_ms, p99_ms, cpu_pct, memory_pct, error_rate) VALUES
('R010', 5000, 10, 44, 56, 62, 60, 0.001);

-- ============================================================
-- Done. Verify with:
--   SELECT COUNT(*) FROM benchmark_runs;     -- expect 10
--   SELECT COUNT(*) FROM benchmark_metrics;  -- expect 10
-- ============================================================
