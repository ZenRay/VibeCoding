"""
L3 Aggregation Analysis Tests - 12 test cases.

Tests aggregation functions (COUNT, SUM, AVG, MIN, MAX) and
GROUP BY/HAVING queries.
Target database: ecommerce_small (small)
"""

import pytest

from tests.contract.test_framework import TestCase, TestCategory

# L3 Test Cases Definition
L3_TEST_CASES = [
    TestCase(
        id="L3.1",
        category=TestCategory.L3_AGGREGATE,
        natural_language="每个类别有多少个产品",
        database="small",
        expected_sql=r"SELECT .* category.* COUNT\(.*\).* FROM products GROUP BY category",
        validation_rules=["has_group_by", "uses_aggregate"],
        description="Basic count with GROUP BY",
    ),
    TestCase(
        id="L3.2",
        category=TestCategory.L3_AGGREGATE,
        natural_language="每个客户的订单总金额",
        database="small",
        expected_sql=(
            r"SELECT .* FROM customers .* LEFT JOIN orders .* "
            r"SUM\(.*total_amount.*\).* GROUP BY .*"
        ),
        validation_rules=["has_join", "has_group_by", "uses_aggregate"],
        description="Sum aggregation with LEFT JOIN",
    ),
    TestCase(
        id="L3.3",
        category=TestCategory.L3_AGGREGATE,
        natural_language="每个类别的平均产品价格",
        database="small",
        expected_sql=r"SELECT .* category.* AVG\(price\).* FROM products GROUP BY category",
        validation_rules=["has_group_by", "uses_aggregate"],
        description="Average value",
    ),
    TestCase(
        id="L3.4",
        category=TestCategory.L3_AGGREGATE,
        natural_language="每个类别的最高和最低价格",
        database="small",
        expected_sql=(
            r"SELECT .* category.* MAX\(price\).* MIN\(price\).* "
            r"FROM products GROUP BY category"
        ),
        validation_rules=["has_group_by", "uses_aggregate"],
        description="MAX and MIN functions",
    ),
    TestCase(
        id="L3.5",
        category=TestCategory.L3_AGGREGATE,
        natural_language="显示订单数超过 5 的客户",
        database="small",
        expected_sql=(
            r"SELECT .* FROM customers .* JOIN orders .* " r"GROUP BY .* HAVING COUNT\(.*\)\s*>\s*5"
        ),
        validation_rules=["has_join", "has_group_by"],
        description="HAVING filter",
    ),
    TestCase(
        id="L3.6",
        category=TestCategory.L3_AGGREGATE,
        natural_language="每个产品的评论数、平均评分和总销量",
        database="small",
        expected_sql=(
            r"SELECT .* FROM products .* LEFT JOIN reviews .* "
            r"LEFT JOIN order_items .* GROUP BY .* "
            r"COUNT\(.*(DISTINCT|review_id).*\).* AVG\(.*rating.*\).* SUM\(.*quantity.*\)"
        ),
        validation_rules=["has_join", "has_group_by", "uses_aggregate"],
        description="Multiple aggregations",
    ),
    TestCase(
        id="L3.7",
        category=TestCategory.L3_AGGREGATE,
        natural_language="每月的订单数量",
        database="small",
        expected_sql=(
            r"SELECT .* DATE_TRUNC\('month',\s*order_date\).* "
            r"COUNT\(.*\).* FROM orders GROUP BY .*DATE_TRUNC"
        ),
        validation_rules=["has_group_by", "uses_aggregate"],
        description="Date grouping with DATE_TRUNC",
    ),
    TestCase(
        id="L3.8",
        category=TestCategory.L3_AGGREGATE,
        natural_language="每个客户的已完成和已取消订单数",
        database="small",
        expected_sql=(
            r"SELECT .* FROM customers .* LEFT JOIN orders .* "
            r"COUNT\(.*CASE WHEN.*status.*=.*'delivered'.*\).* "
            r"COUNT\(.*CASE WHEN.*status.*=.*'cancelled'.*\).* GROUP BY .*"
        ),
        validation_rules=["has_join", "has_group_by", "uses_aggregate"],
        description="Conditional aggregation with CASE",
    ),
    TestCase(
        id="L3.9",
        category=TestCategory.L3_AGGREGATE,
        natural_language="每个类别占总产品数的百分比",
        database="small",
        expected_sql=(
            r"SELECT .* category.* COUNT\(.*\).* "
            r"\(SELECT COUNT\(\*\) FROM products\).* FROM products GROUP BY category"
        ),
        validation_rules=["has_group_by", "uses_aggregate"],
        description="Percentage calculation with subquery",
    ),
    TestCase(
        id="L3.10",
        category=TestCategory.L3_AGGREGATE,
        natural_language="显示销量前 5 的产品",
        database="small",
        expected_sql=(
            r"SELECT .* FROM products .* JOIN order_items .* "
            r"GROUP BY .* SUM\(.*quantity.*\).* ORDER BY .* DESC LIMIT 5"
        ),
        validation_rules=["has_join", "has_group_by", "has_order_by", "has_limit"],
        description="Ranking with aggregation",
    ),
    TestCase(
        id="L3.11",
        category=TestCategory.L3_AGGREGATE,
        natural_language="显示每个类别中价格最高的前 3 个产品",
        database="small",
        expected_sql=(
            r"SELECT .* FROM \(SELECT .* ROW_NUMBER\(\) OVER "
            r"\(PARTITION BY category ORDER BY price DESC\).* "
            r"FROM products\).* WHERE .* <= 3"
        ),
        validation_rules=[],
        description="Window function ROW_NUMBER with PARTITION BY",
    ),
    TestCase(
        id="L3.12",
        category=TestCategory.L3_AGGREGATE,
        natural_language="显示每月的累计订单数",
        database="small",
        expected_sql=(
            r"SELECT .* DATE_TRUNC\('month',\s*order_date\).* COUNT\(.*\).* "
            r"SUM\(COUNT\(.*\)\) OVER \(ORDER BY .*\).* FROM orders GROUP BY .*"
        ),
        validation_rules=["has_group_by", "uses_aggregate"],
        description="Cumulative calculation with window function",
    ),
]


# Pytest parametrize decorator for L3 tests
@pytest.mark.parametrize("test_case", L3_TEST_CASES, ids=lambda tc: tc.id)
@pytest.mark.asyncio
async def test_l3_aggregate_queries(test_case: TestCase) -> None:
    """
    Test L3 aggregation analysis query generation.

    Args:
    ----------
        test_case: Test case definition

    Example:
    ----------
        >>> # Run with pytest
        >>> # pytest tests/contract/test_l3_aggregate.py -v
    """
    # Test implementation will be added in test runner
    pytest.skip("Test case defined, runner not yet implemented")
