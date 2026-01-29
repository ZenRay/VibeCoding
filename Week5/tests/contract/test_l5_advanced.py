"""
L5 Advanced Features Tests - 8 test cases.

Tests PostgreSQL advanced features including CTE, window functions,
LATERAL JOIN, and other sophisticated SQL constructs.
Target database: ecommerce_small (small)
"""

import pytest

from tests.contract.test_framework import TestCase, TestCategory

# L5 Test Cases Definition
L5_TEST_CASES = [
    TestCase(
        id="L5.1",
        category=TestCategory.L5_ADVANCED,
        natural_language="显示订单金额高于该客户平均订单金额的订单",
        database="ecommerce_small",
        expected_sql=(
            r"WITH .* AS \(SELECT .* AVG\(total_amount\).* "
            r"FROM orders GROUP BY customer_id\) SELECT .* FROM orders .* "
            r"JOIN .* WHERE .*total_amount.*>.*avg"
        ),
        validation_rules=[],
        description="CTE (Common Table Expression)",
    ),
    TestCase(
        id="L5.2",
        category=TestCategory.L5_ADVANCED,
        natural_language="显示每个客户的订单数和总消费,以及在所有客户中的排名",
        database="ecommerce_small",
        expected_sql=(
            r"WITH .* AS \(SELECT .* COUNT\(.*\).* SUM\(.*\).* "
            r"FROM customers .* GROUP BY .*\).* AS \(SELECT .* "
            r"ROW_NUMBER\(\) OVER.*ORDER BY.*\)"
        ),
        validation_rules=[],
        description="Multiple CTEs with window function",
    ),
    TestCase(
        id="L5.3",
        category=TestCategory.L5_ADVANCED,
        natural_language="显示每个客户的订单及上一笔和下一笔订单金额",
        database="ecommerce_small",
        expected_sql=(
            r"SELECT .* LAG\(.*total_amount.*\) OVER.*PARTITION BY customer_id.*"
            r"LEAD\(.*total_amount.*\) OVER.*PARTITION BY customer_id"
        ),
        validation_rules=[],
        description="LAG/LEAD window functions",
    ),
    TestCase(
        id="L5.4",
        category=TestCategory.L5_ADVANCED,
        natural_language="每个用户发布的公开和私密帖子数量",
        database="social_medium",
        expected_sql=(
            r"SELECT .* COUNT\(\*\) FILTER \(WHERE privacy.*=.*'public'\).* "
            r"COUNT\(\*\) FILTER \(WHERE privacy.*=.*'private'\).* "
            r"FROM posts GROUP BY user_id"
        ),
        validation_rules=["has_group_by"],
        description="FILTER aggregation",
    ),
    TestCase(
        id="L5.5",
        category=TestCategory.L5_ADVANCED,
        natural_language="显示每个客户的最近 3 笔订单",
        database="ecommerce_small",
        expected_sql=(
            r"SELECT .* FROM customers .* CROSS JOIN LATERAL \(SELECT .* "
            r"FROM orders .* WHERE .*customer_id.*=.*customer_id.* "
            r"ORDER BY .* LIMIT 3\)"
        ),
        validation_rules=[],
        description="LATERAL JOIN",
    ),
    TestCase(
        id="L5.6",
        category=TestCategory.L5_ADVANCED,
        natural_language="显示按类别、按年份、按类别和年份分组的产品数量",
        database="ecommerce_small",
        expected_sql=(
            r"SELECT .* COUNT\(\*\).* FROM products GROUP BY "
            r"GROUPING SETS \(.*category.*EXTRACT\(YEAR FROM created_at\)"
        ),
        validation_rules=["has_group_by"],
        description="GROUPING SETS",
    ),
    TestCase(
        id="L5.7",
        category=TestCategory.L5_ADVANCED,
        natural_language="生成最近 7 天的每日订单统计",
        database="ecommerce_small",
        expected_sql=(
            r"SELECT .* FROM generate_series\(.*CURRENT_DATE.*-.*INTERVAL.*"
            r"CURRENT_DATE.*'1 day'\).* LEFT JOIN orders"
        ),
        validation_rules=[],
        description="generate_series function",
    ),
    TestCase(
        id="L5.8",
        category=TestCategory.L5_ADVANCED,
        natural_language="显示每个订单的产品名称列表(逗号分隔)",
        database="ecommerce_small",
        expected_sql=(
            r"SELECT .* STRING_AGG\(.*name.*,\s*','.*ORDER BY.*\).* "
            r"FROM orders .* JOIN order_items .* JOIN products .* GROUP BY"
        ),
        validation_rules=["has_join", "has_group_by"],
        description="STRING_AGG aggregation",
    ),
]


# Pytest parametrize decorator for L5 tests
@pytest.mark.parametrize("test_case", L5_TEST_CASES, ids=lambda tc: tc.id)
@pytest.mark.asyncio
async def test_l5_advanced_queries(test_case: TestCase) -> None:
    """
    Test L5 advanced features query generation.

    Args:
    ----------
        test_case: Test case definition

    Example:
    ----------
        >>> # Run with pytest
        >>> # pytest tests/contract/test_l5_advanced.py -v
    """
    # Test implementation will be added in test runner
    pytest.skip("Test case defined, runner not yet implemented")
