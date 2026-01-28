"""
L1 Basic Query Tests - 15 test cases.

Tests simple SELECT queries including filtering, sorting, and limits.
Target database: ecommerce_small (small)
"""

import pytest

from tests.contract.test_framework import TestCase, TestCategory

# L1 Test Cases Definition
L1_TEST_CASES = [
    TestCase(
        id="L1.1",
        category=TestCategory.L1_BASIC,
        natural_language="显示所有产品",
        database="small",
        expected_sql=r"SELECT .* FROM products",
        validation_rules=["no_where_clause"],
        description="Simple query all records",
    ),
    TestCase(
        id="L1.2",
        category=TestCategory.L1_BASIC,
        natural_language="显示价格大于 100 的产品",
        database="small",
        expected_sql=r"SELECT .* FROM products WHERE .* price\s*>\s*100",
        validation_rules=["has_where_clause", "uses_comparison"],
        description="Query with condition filter",
    ),
    TestCase(
        id="L1.3",
        category=TestCategory.L1_BASIC,
        natural_language="找出名字包含 'laptop' 的产品",
        database="small",
        expected_sql=r"SELECT .* FROM products WHERE .* (ILIKE|LIKE) .*laptop.*",
        validation_rules=["has_where_clause", "uses_like"],
        description="Fuzzy search with pattern matching",
    ),
    TestCase(
        id="L1.4",
        category=TestCategory.L1_BASIC,
        natural_language="按价格从高到低显示产品",
        database="small",
        expected_sql=r"SELECT .* FROM products ORDER BY price DESC",
        validation_rules=["has_order_by"],
        description="Sorted query",
    ),
    TestCase(
        id="L1.5",
        category=TestCategory.L1_BASIC,
        natural_language="显示前 10 个最贵的产品",
        database="small",
        expected_sql=r"SELECT .* FROM products ORDER BY price DESC LIMIT 10",
        validation_rules=["has_order_by", "has_limit"],
        description="Limit result count with sorting",
    ),
    TestCase(
        id="L1.6",
        category=TestCategory.L1_BASIC,
        natural_language="找出类别是 'Electronics' 且有库存的产品",
        database="small",
        expected_sql=(
            r"SELECT .* FROM products WHERE .* category.*=.*'Electronics'.* "
            r"AND .* stock_quantity\s*>\s*0"
        ),
        validation_rules=["has_where_clause", "uses_and"],
        description="Multiple conditions with AND",
    ),
    TestCase(
        id="L1.7",
        category=TestCategory.L1_BASIC,
        natural_language="显示类别是 'Books' 或 'Toys' 的产品",
        database="small",
        expected_sql=(
            r"SELECT .* FROM products WHERE .*(category.*=.*'Books'.*OR.*"
            r"category.*=.*'Toys'|category IN \('Books',\s*'Toys'\))"
        ),
        validation_rules=["has_where_clause"],
        description="OR condition or IN clause",
    ),
    TestCase(
        id="L1.8",
        category=TestCategory.L1_BASIC,
        natural_language="显示最近 30 天创建的客户",
        database="small",
        expected_sql=(
            r"SELECT .* FROM customers WHERE .* created_at\s*>=\s*.*" r"INTERVAL\s*'30\s*days?'"
        ),
        validation_rules=["has_where_clause", "uses_interval"],
        description="Date range query with INTERVAL",
    ),
    TestCase(
        id="L1.9",
        category=TestCategory.L1_BASIC,
        natural_language="找出没有填写地址的客户",
        database="small",
        expected_sql=r"SELECT .* FROM customers WHERE .* address IS NULL",
        validation_rules=["has_where_clause", "uses_is_null"],
        description="NULL value check",
    ),
    TestCase(
        id="L1.10",
        category=TestCategory.L1_BASIC,
        natural_language="有多少个产品",
        database="small",
        expected_sql=r"SELECT COUNT\(\*\) FROM products",
        validation_rules=["uses_aggregate"],
        description="Count query",
    ),
    TestCase(
        id="L1.11",
        category=TestCategory.L1_BASIC,
        natural_language="显示所有不同的产品类别",
        database="small",
        expected_sql=r"SELECT DISTINCT category FROM products",
        validation_rules=["uses_distinct"],
        description="Distinct query",
    ),
    TestCase(
        id="L1.12",
        category=TestCategory.L1_BASIC,
        natural_language="显示价格在 50 到 200 之间的产品",
        database="small",
        expected_sql=r"SELECT .* FROM products WHERE .* price BETWEEN 50 AND 200",
        validation_rules=["has_where_clause", "uses_between"],
        description="BETWEEN range query",
    ),
    TestCase(
        id="L1.13",
        category=TestCategory.L1_BASIC,
        natural_language="只显示产品名称和价格",
        database="small",
        expected_sql=r"SELECT\s+name\s*,\s*price\s+FROM products",
        validation_rules=["select_specific_columns"],
        description="Specific column selection",
    ),
    TestCase(
        id="L1.14",
        category=TestCategory.L1_BASIC,
        natural_language="显示所有活跃的客户",
        database="small",
        expected_sql=r"SELECT .* FROM customers WHERE .* is_active\s*(=\s*true|=\s*TRUE|\s)",
        validation_rules=["has_where_clause"],
        description="Boolean field query",
    ),
    TestCase(
        id="L1.15",
        category=TestCategory.L1_BASIC,
        natural_language="显示所有待处理的订单",
        database="small",
        expected_sql=r"SELECT .* FROM orders WHERE .* status\s*=\s*'pending'",
        validation_rules=["has_where_clause"],
        description="Enum type query",
    ),
]


# Pytest parametrize decorator for L1 tests
@pytest.mark.parametrize("test_case", L1_TEST_CASES, ids=lambda tc: tc.id)
@pytest.mark.asyncio
async def test_l1_basic_queries(test_case: TestCase) -> None:
    """
    Test L1 basic query generation.

    Args:
    ----------
        test_case: Test case definition

    Example:
    ----------
        >>> # Run with pytest
        >>> # pytest tests/contract/test_l1_basic.py -v
    """
    # Test implementation will be added in test runner
    pytest.skip("Test case defined, runner not yet implemented")
