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
