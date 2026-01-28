"""
Automated test runner for contract testing.

This script executes all defined test cases and generates a comprehensive report.
"""

import asyncio
import time
from pathlib import Path

from postgres_mcp.ai.openai_client import OpenAIClient
from postgres_mcp.config import load_config
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
    config = load_config()
    openai_client = OpenAIClient(config.openai)
    pool_manager = PoolManager(config.databases)
    await pool_manager.initialize()

    schema_inspector = SchemaInspector(pool_manager)
    schema_cache = SchemaCache(schema_inspector)
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
                database_name=test_case.database,
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

    print()

    # Run L2 tests
    print(f"Running {len(L2_TEST_CASES)} L2 Multi-Table Join tests...")
    for test_case in L2_TEST_CASES:
        start_time = time.time()
        try:
            # Generate SQL
            result = await sql_generator.generate(
                natural_language=test_case.natural_language,
                database_name=test_case.database,
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

    # Cleanup
    await pool_manager.close()

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
