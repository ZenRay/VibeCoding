"""
Automated test runner for contract testing.

This script executes all defined test cases and generates a comprehensive report.
"""

# ruff: noqa: E402
# E402: Module level import not at top of file
# We need to clear proxy environment variables BEFORE importing httpx-dependent modules

import asyncio
import os
import time
from pathlib import Path

# CRITICAL: Clear proxy settings BEFORE any imports that might use httpx/requests
# This must be done at module level before OpenAI client is imported
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
from postgres_mcp.core.sql_validator import SQLValidator
from postgres_mcp.db.connection_pool import PoolManager
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
from tests.contract.test_l2_join import L2_TEST_CASES
from tests.contract.test_l3_aggregate import L3_TEST_CASES
from tests.contract.test_l4_complex import L4_TEST_CASES
from tests.contract.test_l5_advanced import L5_TEST_CASES
from tests.contract.test_s1_security import S1_TEST_CASES

# Rate limiting configuration to avoid API throttling
# Adjust based on your API plan (free tier usually has low QPM limits)
REQUEST_DELAY_SECONDS = 1.5  # Delay between each test case (40 requests/min)
BATCH_DELAY_SECONDS = 5.0  # Delay between test categories


async def run_contract_tests() -> TestReport:
    """
    Run all contract tests and generate report.

    Returns:
    ----------
        Test report with all results

    Example:
    ----------
        >>> report = await run_contract_tests()
        >>> print(report.format_text())
    """
    report = TestReport()
    report.start_time = time.time()

    # Initialize components
    config = Config.load()
    openai_client = OpenAIClient(config.openai)
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

    schema_cache = SchemaCache(inspectors)
    await schema_cache.initialize()

    sql_validator = SQLValidator()
    sql_generator = SQLGenerator(
        openai_client=openai_client,
        schema_cache=schema_cache,
        sql_validator=sql_validator,
    )

    test_validator = TestValidator()

    print("=" * 70)
    print("PostgreSQL MCP Contract Testing")
    print("=" * 70)
    print()

    # Run L1 tests
    print(f"Running {len(L1_TEST_CASES)} L1 Basic Query tests...")
    for test_case in L1_TEST_CASES:
        start_time = time.time()
        try:
            # Generate SQL
            result = await sql_generator.generate(
                natural_language=test_case.natural_language,
                database=test_case.database,
            )

            execution_time = (time.time() - start_time) * 1000

            # Validate SQL
            if test_case.expected_sql:
                pattern_match = test_validator.matches_pattern(result.sql, test_case.expected_sql)
            else:
                pattern_match = True

            # Security validation
            is_safe, security_msg = test_validator.validate_security(result.sql)

            # Check validation rules
            validation_results = {}
            if test_case.validation_rules:
                validation_results = test_validator.check_validation_rules(
                    result.sql, test_case.validation_rules
                )

            # Determine status
            if not is_safe:
                status = TestStatus.FAILED
                error_msg = f"Security violation: {security_msg}"
            elif not pattern_match:
                status = TestStatus.FAILED
                error_msg = "SQL pattern does not match expected"
            elif validation_results and not all(validation_results.values()):
                status = TestStatus.FAILED
                failed_rules = [k for k, v in validation_results.items() if not v]
                error_msg = f"Validation failed for rules: {', '.join(failed_rules)}"
            else:
                status = TestStatus.PASSED
                error_msg = None

            test_result = TestResult(
                test_id=test_case.id,
                status=status,
                generated_sql=result.sql,
                execution_time_ms=execution_time,
                error_message=error_msg,
                validation_details={
                    "pattern_match": pattern_match,
                    "security_check": is_safe,
                    "validation_rules": validation_results,
                },
            )

            # Print status
            status_symbol = "✓" if status == TestStatus.PASSED else "✗"
            print(f"  {status_symbol} {test_case.id}: {status.value}")
            if error_msg:
                print(f"    Error: {error_msg}")
                print(f"    Generated: {result.sql[:80]}...")

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

        # Rate limiting delay
        await asyncio.sleep(REQUEST_DELAY_SECONDS)

    print()

    # Delay between test categories
    print(f"⏳ Waiting {BATCH_DELAY_SECONDS}s before next category (rate limiting)...")
    await asyncio.sleep(BATCH_DELAY_SECONDS)
    print()

    # Run L2 tests
    print(f"Running {len(L2_TEST_CASES)} L2 Multi-Table Join tests...")
    for test_case in L2_TEST_CASES:
        start_time = time.time()
        try:
            # Generate SQL
            result = await sql_generator.generate(
                natural_language=test_case.natural_language,
                database=test_case.database,
            )

            execution_time = (time.time() - start_time) * 1000

            # Validate SQL
            if test_case.expected_sql:
                pattern_match = test_validator.matches_pattern(result.sql, test_case.expected_sql)
            else:
                pattern_match = True

            # Security validation
            is_safe, security_msg = test_validator.validate_security(result.sql)

            # Check validation rules
            validation_results = {}
            if test_case.validation_rules:
                validation_results = test_validator.check_validation_rules(
                    result.sql, test_case.validation_rules
                )

            # Determine status
            if not is_safe:
                status = TestStatus.FAILED
                error_msg = f"Security violation: {security_msg}"
            elif not pattern_match:
                status = TestStatus.FAILED
                error_msg = "SQL pattern does not match expected"
            elif validation_results and not all(validation_results.values()):
                status = TestStatus.FAILED
                failed_rules = [k for k, v in validation_results.items() if not v]
                error_msg = f"Validation failed for rules: {', '.join(failed_rules)}"
            else:
                status = TestStatus.PASSED
                error_msg = None

            test_result = TestResult(
                test_id=test_case.id,
                status=status,
                generated_sql=result.sql,
                execution_time_ms=execution_time,
                error_message=error_msg,
                validation_details={
                    "pattern_match": pattern_match,
                    "security_check": is_safe,
                    "validation_rules": validation_results,
                },
            )

            # Print status
            status_symbol = "✓" if status == TestStatus.PASSED else "✗"
            print(f"  {status_symbol} {test_case.id}: {status.value}")
            if error_msg:
                print(f"    Error: {error_msg}")
                print(f"    Generated: {result.sql[:80]}...")

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

        # Rate limiting delay
        await asyncio.sleep(REQUEST_DELAY_SECONDS)

    print()

    # Delay between test categories
    print(f"⏳ Waiting {BATCH_DELAY_SECONDS}s before next category (rate limiting)...")
    await asyncio.sleep(BATCH_DELAY_SECONDS)
    print()

    # Run L3 tests
    print(f"Running {len(L3_TEST_CASES)} L3 Aggregation Analysis tests...")
    for test_case in L3_TEST_CASES:
        start_time = time.time()
        try:
            # Generate SQL
            result = await sql_generator.generate(
                natural_language=test_case.natural_language,
                database=test_case.database,
            )

            execution_time = (time.time() - start_time) * 1000

            # Validate SQL
            if test_case.expected_sql:
                pattern_match = test_validator.matches_pattern(result.sql, test_case.expected_sql)
            else:
                pattern_match = True

            # Security validation
            is_safe, security_msg = test_validator.validate_security(result.sql)

            # Check validation rules
            validation_results = {}
            if test_case.validation_rules:
                validation_results = test_validator.check_validation_rules(
                    result.sql, test_case.validation_rules
                )

            # Determine status
            if not is_safe:
                status = TestStatus.FAILED
                error_msg = f"Security violation: {security_msg}"
            elif not pattern_match:
                status = TestStatus.FAILED
                error_msg = "SQL pattern does not match expected"
            elif validation_results and not all(validation_results.values()):
                status = TestStatus.FAILED
                failed_rules = [k for k, v in validation_results.items() if not v]
                error_msg = f"Validation failed for rules: {', '.join(failed_rules)}"
            else:
                status = TestStatus.PASSED
                error_msg = None

            test_result = TestResult(
                test_id=test_case.id,
                status=status,
                generated_sql=result.sql,
                execution_time_ms=execution_time,
                error_message=error_msg,
                validation_details={
                    "pattern_match": pattern_match,
                    "security_check": is_safe,
                    "validation_rules": validation_results,
                },
            )

            # Print status
            status_symbol = "✓" if status == TestStatus.PASSED else "✗"
            print(f"  {status_symbol} {test_case.id}: {status.value}")
            if error_msg:
                print(f"    Error: {error_msg}")
                print(f"    Generated: {result.sql[:80]}...")

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

        # Rate limiting delay
        await asyncio.sleep(REQUEST_DELAY_SECONDS)

    print()

    # Delay between test categories
    print(f"⏳ Waiting {BATCH_DELAY_SECONDS}s before next category (rate limiting)...")
    await asyncio.sleep(BATCH_DELAY_SECONDS)
    print()

    # Run L4 tests
    print(f"Running {len(L4_TEST_CASES)} L4 Complex Logic tests...")
    for test_case in L4_TEST_CASES:
        start_time = time.time()
        try:
            result = await sql_generator.generate(
                natural_language=test_case.natural_language,
                database=test_case.database,
            )
            execution_time = (time.time() - start_time) * 1000

            if test_case.expected_sql:
                pattern_match = test_validator.matches_pattern(result.sql, test_case.expected_sql)
            else:
                pattern_match = True

            is_safe, security_msg = test_validator.validate_security(result.sql)
            validation_results = {}
            if test_case.validation_rules:
                validation_results = test_validator.check_validation_rules(
                    result.sql, test_case.validation_rules
                )

            if not is_safe:
                status = TestStatus.FAILED
                error_msg = f"Security violation: {security_msg}"
            elif not pattern_match:
                status = TestStatus.FAILED
                error_msg = "SQL pattern does not match expected"
            elif validation_results and not all(validation_results.values()):
                status = TestStatus.FAILED
                failed_rules = [k for k, v in validation_results.items() if not v]
                error_msg = f"Validation failed for rules: {', '.join(failed_rules)}"
            else:
                status = TestStatus.PASSED
                error_msg = None

            test_result = TestResult(
                test_id=test_case.id,
                status=status,
                generated_sql=result.sql,
                execution_time_ms=execution_time,
                error_message=error_msg,
                validation_details={
                    "pattern_match": pattern_match,
                    "security_check": is_safe,
                    "validation_rules": validation_results,
                },
            )

            status_symbol = "✓" if status == TestStatus.PASSED else "✗"
            print(f"  {status_symbol} {test_case.id}: {status.value}")
            if error_msg:
                print(f"    Error: {error_msg}")
                print(f"    Generated: {result.sql[:80]}...")

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

        # Rate limiting delay
        await asyncio.sleep(REQUEST_DELAY_SECONDS)

    print()

    # Delay between test categories
    print(f"⏳ Waiting {BATCH_DELAY_SECONDS}s before next category (rate limiting)...")
    await asyncio.sleep(BATCH_DELAY_SECONDS)
    print()

    # Run L5 tests
    print(f"Running {len(L5_TEST_CASES)} L5 Advanced Features tests...")
    for test_case in L5_TEST_CASES:
        start_time = time.time()
        try:
            result = await sql_generator.generate(
                natural_language=test_case.natural_language,
                database=test_case.database,
            )
            execution_time = (time.time() - start_time) * 1000

            if test_case.expected_sql:
                pattern_match = test_validator.matches_pattern(result.sql, test_case.expected_sql)
            else:
                pattern_match = True

            is_safe, security_msg = test_validator.validate_security(result.sql)
            validation_results = {}
            if test_case.validation_rules:
                validation_results = test_validator.check_validation_rules(
                    result.sql, test_case.validation_rules
                )

            if not is_safe:
                status = TestStatus.FAILED
                error_msg = f"Security violation: {security_msg}"
            elif not pattern_match:
                status = TestStatus.FAILED
                error_msg = "SQL pattern does not match expected"
            elif validation_results and not all(validation_results.values()):
                status = TestStatus.FAILED
                failed_rules = [k for k, v in validation_results.items() if not v]
                error_msg = f"Validation failed for rules: {', '.join(failed_rules)}"
            else:
                status = TestStatus.PASSED
                error_msg = None

            test_result = TestResult(
                test_id=test_case.id,
                status=status,
                generated_sql=result.sql,
                execution_time_ms=execution_time,
                error_message=error_msg,
                validation_details={
                    "pattern_match": pattern_match,
                    "security_check": is_safe,
                    "validation_rules": validation_results,
                },
            )

            status_symbol = "✓" if status == TestStatus.PASSED else "✗"
            print(f"  {status_symbol} {test_case.id}: {status.value}")
            if error_msg:
                print(f"    Error: {error_msg}")
                print(f"    Generated: {result.sql[:80]}...")

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

        # Rate limiting delay
        await asyncio.sleep(REQUEST_DELAY_SECONDS)

    print()

    # Delay between test categories
    print(f"⏳ Waiting {BATCH_DELAY_SECONDS}s before next category (rate limiting)...")
    await asyncio.sleep(BATCH_DELAY_SECONDS)
    print()

    # Run S1 security tests
    print(f"Running {len(S1_TEST_CASES)} S1 Security tests...")
    for test_case in S1_TEST_CASES:
        start_time = time.time()
        try:
            result = await sql_generator.generate(
                natural_language=test_case.natural_language,
                database=test_case.database,
            )
            execution_time = (time.time() - start_time) * 1000

            # Security tests have special validation logic
            is_safe, security_msg = test_validator.validate_security(result.sql)

            if test_case.expected_behavior == "REJECT":
                # Should be rejected - security violation expected
                if not is_safe:
                    status = TestStatus.PASSED
                    error_msg = None
                else:
                    status = TestStatus.FAILED
                    error_msg = "Expected security rejection but query was allowed"
            elif test_case.expected_behavior == "SANITIZE":
                # Should be sanitized - check if SQL is safe and matches pattern
                if not is_safe:
                    status = TestStatus.FAILED
                    error_msg = f"Generated unsafe SQL: {security_msg}"
                elif test_case.expected_sql:
                    pattern_match = test_validator.matches_pattern(
                        result.sql, test_case.expected_sql
                    )
                    if pattern_match:
                        status = TestStatus.PASSED
                        error_msg = None
                    else:
                        status = TestStatus.FAILED
                        error_msg = "SQL pattern does not match expected (sanitization failed)"
                else:
                    status = TestStatus.PASSED
                    error_msg = None
            else:
                # Standard security check
                if is_safe:
                    status = TestStatus.PASSED
                    error_msg = None
                else:
                    status = TestStatus.FAILED
                    error_msg = f"Security violation: {security_msg}"

            test_result = TestResult(
                test_id=test_case.id,
                status=status,
                generated_sql=result.sql if is_safe else "[BLOCKED]",
                execution_time_ms=execution_time,
                error_message=error_msg,
                validation_details={
                    "security_check": is_safe,
                    "expected_behavior": test_case.expected_behavior,
                    "security_message": security_msg if not is_safe else None,
                },
            )

            status_symbol = "✓" if status == TestStatus.PASSED else "✗"
            print(f"  {status_symbol} {test_case.id}: {status.value}")
            if error_msg:
                print(f"    Error: {error_msg}")
                if is_safe:
                    print(f"    Generated: {result.sql[:80]}...")

        except Exception as e:
            # Security tests may intentionally cause exceptions
            error_str = str(e).lower()
            if any(
                keyword in error_str
                for keyword in ["drop", "delete", "update", "insert", "alter", "truncate"]
            ):
                # Expected security exception
                test_result = TestResult(
                    test_id=test_case.id,
                    status=TestStatus.PASSED,
                    generated_sql="[BLOCKED BY VALIDATOR]",
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error_message=None,
                    validation_details={
                        "security_check": False,
                        "blocked_by_validator": True,
                        "validator_message": str(e),
                    },
                )
                print(f"  ✓ {test_case.id}: PASSED (blocked by validator)")
            else:
                # Unexpected exception
                test_result = TestResult(
                    test_id=test_case.id,
                    status=TestStatus.FAILED,
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error_message=str(e),
                )
                print(f"  ✗ {test_case.id}: FAILED")
                print(f"    Error: {str(e)}")

        report.add_result(test_result)

        # Rate limiting delay
        await asyncio.sleep(REQUEST_DELAY_SECONDS)

    print()

    # Cleanup
    await pool_manager.close_all()
    # Note: Skipping inspector cleanup due to API compatibility
    # for inspector in inspectors.values():
    #     await inspector.disconnect()

    report.end_time = time.time()
    return report


async def main() -> None:
    """
    Main entry point for contract testing.

    Example:
    ----------
        >>> # Run from command line
        >>> # python -m tests.contract.run_tests
    """
    try:
        report = await run_contract_tests()

        print()
        print("=" * 70)
        print("Test Summary")
        print("=" * 70)
        summary = report.get_summary()
        print(f"Total Tests: {summary['total']}")
        print(f"Passed: {summary['passed']} ({summary['pass_rate']:.1f}%)")
        print(f"Failed: {summary['failed']}")
        print(f"Skipped: {summary['skipped']}")

        # Save report
        output_dir = Path("test_reports")
        output_dir.mkdir(exist_ok=True)

        report_file = output_dir / "contract_test_report.txt"
        report_file.write_text(report.format_text())
        print()
        print(f"Report saved to: {report_file}")

        # Exit with appropriate code
        exit_code = 0 if summary["failed"] == 0 else 1
        exit(exit_code)

    except Exception as e:
        print(f"Test runner failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
