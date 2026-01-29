"""
Modular test runner for contract testing - run specific test categories.

This module allows running selected test categories instead of all tests.
"""

# ruff: noqa: E402
import asyncio
import os
import time
from pathlib import Path

# Clear proxy settings before imports
for proxy_var in [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
]:
    os.environ.pop(proxy_var, None)

from postgres_mcp.ai.openai_client import OpenAIClient
from postgres_mcp.config import Config
from postgres_mcp.core.schema_cache import SchemaCache
from postgres_mcp.core.sql_generator import SQLGenerator
from postgres_mcp.db.connection_pool import PoolManager
from postgres_mcp.db.schema_inspector import SchemaInspector
from tests.contract.test_framework import (
    SQLValidator as TestValidator,
)
from tests.contract.test_framework import (
    TestCase,
    TestCategory,
    TestReport,
    TestResult,
    TestStatus,
)
from tests.contract.test_l1_basic import L1_TEST_CASES
from tests.contract.test_l2_join import L2_TEST_CASES
from tests.contract.test_l3_aggregate import L3_TEST_CASES
from tests.contract.test_l4_complex import L4_TEST_CASES
from tests.contract.test_l5_advanced import L5_TEST_CASES
from tests.contract.test_s1_security import S1_TEST_CASES

# Rate limiting
REQUEST_DELAY_SECONDS = 1.5
BATCH_DELAY_SECONDS = 5.0

# Module mapping
TEST_MODULES = {
    "L1": (TestCategory.L1_BASIC, L1_TEST_CASES, "L1 Basic Query"),
    "L2": (TestCategory.L2_JOIN, L2_TEST_CASES, "L2 Multi-Table JOIN"),
    "L3": (TestCategory.L3_AGGREGATE, L3_TEST_CASES, "L3 Aggregation"),
    "L4": (TestCategory.L4_COMPLEX, L4_TEST_CASES, "L4 Complex Logic"),
    "L5": (TestCategory.L5_ADVANCED, L5_TEST_CASES, "L5 Advanced Features"),
    "S1": (TestCategory.S1_SECURITY, S1_TEST_CASES, "S1 Security"),
}


async def run_test_case(
    test_case: TestCase, sql_generator: SQLGenerator, test_validator: TestValidator
) -> TestResult:
    """Run a single test case."""
    start_time = time.time()
    
    try:
        # Generate SQL
        response = await sql_generator.generate(
            natural_language=test_case.natural_language,
            database=test_case.database,
        )
        
        execution_time = (time.time() - start_time) * 1000

        # Validate
        if test_case.expected_behavior == "reject":
            # Security test - should reject
            if response.sql:
                status = TestStatus.FAILED
                error_msg = "Expected security rejection but query was allowed"
            else:
                status = TestStatus.PASSED
                error_msg = None
        else:
            # Normal test - should pass pattern match
            is_match = test_validator.matches_pattern(response.sql, test_case.expected_sql)
            validation_results = test_validator.check_validation_rules(
                response.sql, test_case.validation_rules
            )
            rules_pass = all(validation_results.values()) if validation_results else True
            failed_rules = [k for k, v in validation_results.items() if not v] if validation_results else []

            if is_match and rules_pass:
                status = TestStatus.PASSED
                error_msg = None
            else:
                status = TestStatus.FAILED
                errors = []
                if not is_match:
                    errors.append("SQL pattern does not match expected")
                if not rules_pass:
                    errors.append(f"Validation failed for rules: {', '.join(failed_rules)}")
                error_msg = "; ".join(errors)

        test_result = TestResult(
            test_id=test_case.id,
            status=status,
            generated_sql=response.sql,
            execution_time_ms=execution_time,
            error_message=error_msg,
            validation_details={
                "pattern_match": is_match if test_case.expected_behavior != "reject" else None,
                "validation_rules": test_case.validation_rules,
            },
        )

    except Exception as e:
        test_result = TestResult(
            test_id=test_case.id,
            status=TestStatus.FAILED,
            execution_time_ms=(time.time() - start_time) * 1000,
            error_message=f"AI service unavailable: {e}",
        )

    return test_result


async def run_selected_modules(module_names: list[str]) -> None:
    """
    Run tests for selected modules.

    Args:
    ----------
        module_names: List of module names to run (e.g., ['L1', 'L2'])
    """
    report = TestReport()
    report.start_time = time.time()

    # Initialize components
    config = Config.load()
    openai_client = OpenAIClient(
        api_key=config.openai.api_key,
        model=config.openai.model,
        base_url=config.openai.base_url,
        timeout=config.openai.timeout,
    )
    pool_manager = PoolManager(config.databases)
    await pool_manager.initialize()

    # Create SchemaInspector for each database
    inspectors = {}
    for db_config in config.databases:
        # Resolve password from env var
        password = db_config.password
        if db_config.password_env_var:
            import os

            password = os.environ.get(db_config.password_env_var, "")

        inspector = SchemaInspector(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=password,
            database=db_config.database,
        )
        inspectors[db_config.name] = inspector

    # Initialize schema cache
    schema_cache = SchemaCache(inspectors)
    await schema_cache.initialize()

    # Create SQL generator and validator
    from postgres_mcp.core.sql_validator import SQLValidator as ProductionValidator

    sql_validator = ProductionValidator()
    sql_generator = SQLGenerator(
        openai_client=openai_client,
        schema_cache=schema_cache,
        sql_validator=sql_validator,
    )
    test_validator = TestValidator()

    print("=" * 70)
    print("PostgreSQL MCP Contract Testing - Selected Modules")
    print("=" * 70)
    print()

    # Run selected modules
    for module_name in module_names:
        if module_name not in TEST_MODULES:
            print(f"⚠️  Unknown module: {module_name}")
            continue

        category, test_cases, display_name = TEST_MODULES[module_name]

        print(f"Running {len(test_cases)} {display_name} tests...")

        for i, test_case in enumerate(test_cases, 1):
            result = await run_test_case(test_case, sql_generator, test_validator)
            report.add_result(result)

            # Display result
            status_icon = "✓" if result.status == TestStatus.PASSED else "✗"
            print(f"  {status_icon} {result.test_id}: {result.status.value.upper()}")

            if result.status == TestStatus.FAILED and result.error_message:
                print(f"    Error: {result.error_message}")
                if result.generated_sql:
                    preview = result.generated_sql[:80] + (
                        "..." if len(result.generated_sql) > 80 else ""
                    )
                    print(f"    Generated: {preview}")

            # Rate limiting
            if i < len(test_cases):
                await asyncio.sleep(REQUEST_DELAY_SECONDS)

        print()

        # Delay between categories
        if module_name != module_names[-1]:
            print(f"⏳ Waiting {BATCH_DELAY_SECONDS}s before next category (rate limiting)...")
            print()
            await asyncio.sleep(BATCH_DELAY_SECONDS)

    # Finalize
    report.end_time = time.time()

    # Print summary
    print()
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total Tests: {report.total_tests}")
    print(f"Passed: {report.passed_tests} ({report.pass_rate:.1f}%)")
    print(f"Failed: {report.failed_tests}")
    print(f"Skipped: {report.skipped_tests}")
    print()

    # Save report
    report_dir = Path("test_reports")
    report_dir.mkdir(exist_ok=True)
    report_path = report_dir / "contract_test_report.txt"
    report_path.write_text(report.format_text())
    print(f"Report saved to: {report_path}")
    print()

    # Cleanup
    for inspector in inspectors.values():
        await inspector.disconnect()
    pool_manager.close_all()

    print("✅ Test execution complete!")
    modules_str = "+".join(module_names)
    print(f"📄 Results saved to /tmp/contract_test_results_{modules_str.lower()}.txt")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m tests.contract.run_tests_module L1 L2 ...")
        print("Available modules: L1, L2, L3, L4, L5, S1")
        sys.exit(1)

    modules = sys.argv[1:]
    asyncio.run(run_selected_modules(modules))
