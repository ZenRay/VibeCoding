"""
Performance benchmark for SQL security validator.

This script measures the performance characteristics of the SQLValidator
to ensure it meets production requirements.

Run with:
    python benchmark_sql_validator.py
"""

import time
import statistics
from typing import Callable
from sql_validator import SQLValidator


def benchmark(func: Callable, iterations: int = 1000) -> dict[str, float]:
    """
    Benchmark a function by running it multiple times.

    Args:
        func: Function to benchmark
        iterations: Number of iterations to run

    Returns:
        Dictionary with timing statistics (mean, median, min, max, std)
    """
    times = []

    for _ in range(iterations):
        start = time.perf_counter()
        func()
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to milliseconds

    return {
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "std_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "p95_ms": sorted(times)[int(len(times) * 0.95)],
        "p99_ms": sorted(times)[int(len(times) * 0.99)],
    }


def main():
    """Run comprehensive performance benchmarks."""
    validator = SQLValidator(dialect="postgres")

    print("=" * 80)
    print("SQL SECURITY VALIDATOR PERFORMANCE BENCHMARK")
    print("=" * 80)

    # Test queries of varying complexity
    test_cases = [
        (
            "Simple SELECT",
            "SELECT * FROM users",
        ),
        (
            "SELECT with WHERE",
            "SELECT id, name FROM users WHERE active = true AND role = 'admin'",
        ),
        (
            "SELECT with JOIN",
            """
            SELECT u.id, u.name, o.order_id, o.total
            FROM users u
            INNER JOIN orders o ON u.id = o.user_id
            WHERE u.active = true AND o.status = 'completed'
            """,
        ),
        (
            "SELECT with subquery",
            """
            SELECT * FROM users
            WHERE id IN (
                SELECT user_id FROM orders WHERE total > 1000
            )
            """,
        ),
        (
            "SELECT with CTE",
            """
            WITH active_users AS (
                SELECT id, name FROM users WHERE active = true
            )
            SELECT * FROM active_users WHERE name LIKE 'A%'
            """,
        ),
        (
            "Complex query (multiple CTEs + JOINs)",
            """
            WITH
                active_users AS (
                    SELECT id, name, email FROM users WHERE active = true
                ),
                recent_orders AS (
                    SELECT user_id, COUNT(*) as order_count, SUM(total) as total_spent
                    FROM orders
                    WHERE created_at > CURRENT_DATE - INTERVAL '30 days'
                    GROUP BY user_id
                ),
                user_stats AS (
                    SELECT
                        au.id,
                        au.name,
                        au.email,
                        COALESCE(ro.order_count, 0) as recent_orders,
                        COALESCE(ro.total_spent, 0) as recent_spending
                    FROM active_users au
                    LEFT JOIN recent_orders ro ON au.id = ro.user_id
                )
            SELECT * FROM user_stats
            WHERE recent_orders > 5 OR recent_spending > 1000
            ORDER BY recent_spending DESC
            LIMIT 100
            """,
        ),
        (
            "Very long query (100 columns)",
            "SELECT " + ", ".join([f"col{i}" for i in range(100)]) + " FROM users",
        ),
        (
            "Deeply nested (10 levels)",
            (
                "SELECT * FROM users"
                if True
                else (lambda: sum([f"SELECT * FROM ({sql}) AS level{i}" for i in range(10)]))()
            ),
        ),
    ]

    # Generate deeply nested query properly
    nested_sql = "SELECT * FROM users"
    for i in range(10):
        nested_sql = f"SELECT * FROM ({nested_sql}) AS level{i}"
    test_cases[-1] = ("Deeply nested (10 levels)", nested_sql)

    # Run benchmarks
    results = []
    for name, sql in test_cases:
        print(f"\n{name}")
        print("-" * 80)
        print(f"Query: {sql[:100]}{'...' if len(sql) > 100 else ''}")
        print(f"Query length: {len(sql)} characters")

        # Benchmark validation
        stats = benchmark(lambda: validator.validate(sql), iterations=1000)

        print(f"\nTiming (1000 iterations):")
        print(f"  Mean:   {stats['mean_ms']:.3f} ms")
        print(f"  Median: {stats['median_ms']:.3f} ms")
        print(f"  Min:    {stats['min_ms']:.3f} ms")
        print(f"  Max:    {stats['max_ms']:.3f} ms")
        print(f"  Std:    {stats['std_ms']:.3f} ms")
        print(f"  P95:    {stats['p95_ms']:.3f} ms")
        print(f"  P99:    {stats['p99_ms']:.3f} ms")

        # Calculate theoretical throughput
        queries_per_second = 1000 / stats["mean_ms"]
        print(f"\nTheoretical throughput: {queries_per_second:.0f} queries/second")

        results.append((name, stats))

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print("\nValidation time by query complexity:")
    print(f"{'Query Type':<40} {'Mean (ms)':<12} {'P95 (ms)':<12} {'QPS':<10}")
    print("-" * 80)

    for name, stats in results:
        qps = 1000 / stats["mean_ms"]
        print(f"{name:<40} {stats['mean_ms']:<12.3f} {stats['p95_ms']:<12.3f} {qps:<10.0f}")

    # Overall statistics
    all_means = [stats["mean_ms"] for _, stats in results]
    overall_mean = statistics.mean(all_means)
    overall_median = statistics.median(all_means)

    print("\n" + "=" * 80)
    print("OVERALL STATISTICS")
    print("=" * 80)
    print(f"Average mean validation time: {overall_mean:.3f} ms")
    print(f"Median mean validation time: {overall_median:.3f} ms")
    print(f"Average throughput: {1000 / overall_mean:.0f} queries/second")

    # Performance assessment
    print("\n" + "=" * 80)
    print("PERFORMANCE ASSESSMENT")
    print("=" * 80)

    if overall_mean < 5:
        print("✓ EXCELLENT: Validation time < 5ms")
        print("  Suitable for high-throughput APIs (>1000 QPS)")
    elif overall_mean < 10:
        print("✓ GOOD: Validation time < 10ms")
        print("  Suitable for typical web applications (>500 QPS)")
    elif overall_mean < 20:
        print("⚠ ACCEPTABLE: Validation time < 20ms")
        print("  May need caching for high-traffic applications")
    else:
        print("✗ SLOW: Validation time > 20ms")
        print("  Optimization or caching strongly recommended")

    print("\nRecommendations:")
    if overall_mean < 10:
        print("  - No optimization needed for typical workloads")
        print("  - Consider LRU caching if query patterns are repetitive")
    else:
        print("  - Implement LRU cache for repeated queries")
        print("  - Consider query complexity limits")
        print("  - Profile SQLGlot parsing performance")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
