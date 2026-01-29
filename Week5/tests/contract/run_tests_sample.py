"""
Quick sample test runner for validation.

Tests only 3 cases from L1 to verify the setup.
"""

# ruff: noqa: E402
# E402: Module level import not at top of file
# We need to clear proxy environment variables BEFORE importing httpx-dependent modules

import asyncio
import os
import time

# Clear proxy environment variables BEFORE any imports
for var in [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
]:
    os.environ.pop(var, None)

from postgres_mcp.ai.openai_client import OpenAIClient
from postgres_mcp.config import Config
from postgres_mcp.core.schema_cache import SchemaCache
from postgres_mcp.core.sql_generator import SQLGenerator
from postgres_mcp.core.sql_validator import SQLValidator
from postgres_mcp.db.schema_inspector import SchemaInspector
from tests.contract.test_framework import (
    SQLValidator as TestValidator,
)
from tests.contract.test_framework import (
    TestReport,
    TestResult,
    TestStatus,
)
from tests.contract.test_l1_basic import L1_TEST_CASES

REQUEST_DELAY_SECONDS = 2.0  # Slower for testing


async def main():
    """Run sample contract tests."""
    print("=" * 70)
    print("PostgreSQL MCP Sample Contract Testing (3 test cases)")
    print("=" * 70)
    print()

    # Initialize
    config = Config.load()
    openai_client = OpenAIClient(
        api_key=config.openai.api_key,
        model=config.openai.model,
        base_url=config.openai.base_url,
        timeout=config.openai.timeout,
    )

    # Create SchemaInspector for each database
    inspectors = {}
    for db_config in config.databases:
        password = db_config.password
        if db_config.password_env_var:
            password = os.environ.get(db_config.password_env_var, "")

        inspector = SchemaInspector(
            host=db_config.host,
            port=db_config.port,
            user=db_config.user,
            password=password,
            database=db_config.database,
        )
        inspectors[db_config.name] = inspector

    schema_cache = SchemaCache(inspectors)
    await schema_cache.initialize()

    sql_validator = SQLValidator()
    sql_generator = SQLGenerator(
        openai_client=openai_client,
        schema_cache=schema_cache,
        sql_validator=sql_validator,
    )

    test_validator = TestValidator()
    report = TestReport()
    report.start_time = time.time()

    # Run only first 3 L1 tests
    print("Running 3 sample L1 Basic Query tests...")
    for test_case in L1_TEST_CASES[:3]:
        start_time = time.time()
        try:
            result = await sql_generator.generate(
                natural_language=test_case.natural_language,
                database=test_case.database,
            )

            execution_time = (time.time() - start_time) * 1000

            # Validate
            if test_case.expected_sql:
                pattern_match = test_validator.matches_pattern(result.sql, test_case.expected_sql)
            else:
                pattern_match = True

            is_safe, security_msg = test_validator.validate_security(result.sql)

            if pattern_match and is_safe:
                status = TestStatus.PASSED
                error_msg = None
            else:
                status = TestStatus.FAILED
                error_msg = "Pattern mismatch" if not pattern_match else f"Security: {security_msg}"

            test_result = TestResult(
                test_id=test_case.id,
                status=status,
                generated_sql=result.sql,
                execution_time_ms=execution_time,
                error_message=error_msg,
                validation_details={},
            )

            status_symbol = "✓" if status == TestStatus.PASSED else "✗"
            print(f"  {status_symbol} {test_case.id}: {status.value} ({execution_time:.0f}ms)")
            if error_msg:
                print(f"    Error: {error_msg}")
            print(f"    SQL: {result.sql[:100]}...")

        except Exception as e:
            test_result = TestResult(
                test_id=test_case.id,
                status=TestStatus.FAILED,
                execution_time_ms=(time.time() - start_time) * 1000,
                error_message=str(e),
            )
            print(f"  ✗ {test_case.id}: FAILED")
            print(f"    Error: {str(e)}")

        report.add_result(test_result)
        await asyncio.sleep(REQUEST_DELAY_SECONDS)

    # Cleanup
    # Note: Skipping inspector cleanup due to API compatibility
    # for inspector in inspectors.values():
    #     await inspector.disconnect()

    report.end_time = time.time()

    # Print summary
    print()
    print("=" * 70)
    print(report.format_text())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest runner failed: {e}")
        import traceback

        traceback.print_exc()
