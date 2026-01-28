"""
L2 Multi-Table Join Tests - 15 test cases.

Tests JOIN queries including INNER/LEFT/RIGHT JOIN and foreign key
relationship recognition.
Target databases: ecommerce_small (small), social_medium (medium),
erp_large (large)
"""

import pytest

from tests.contract.test_framework import TestCase, TestCategory

# L2 Test Cases Definition
L2_TEST_CASES = [
    TestCase(
        id="L2.1",
        category=TestCategory.L2_JOIN,
        natural_language="显示所有订单及其客户名字",
        database="small",
        expected_sql=(
            r"SELECT .* FROM orders .* (INNER )?JOIN customers .* " r"ON .*customer_id.*"
        ),
        validation_rules=["has_join"],
        description="Simple inner join",
    ),
    TestCase(
        id="L2.2",
        category=TestCategory.L2_JOIN,
        natural_language="显示所有客户及其订单数量,包括没有订单的客户",
        database="small",
        expected_sql=(
            r"SELECT .* FROM customers .* LEFT JOIN orders .* " r"ON .*customer_id.* GROUP BY .*"
        ),
        validation_rules=["has_join", "has_group_by", "uses_aggregate"],
        description="Left join with count",
    ),
    TestCase(
        id="L2.3",
        category=TestCategory.L2_JOIN,
        natural_language="显示每个订单中的产品名称",
        database="small",
        expected_sql=(r"SELECT .* FROM orders .* JOIN .* order_items .* " r"JOIN .* products .*"),
        validation_rules=["has_join"],
        description="Three-table join",
    ),
    TestCase(
        id="L2.4",
        category=TestCategory.L2_JOIN,
        natural_language="显示所有员工及其经理名字",
        database="large",
        expected_sql=(r"SELECT .* FROM employees .* LEFT JOIN employees .* " r"ON .*manager_id.*"),
        validation_rules=["has_join"],
        description="Self join",
    ),
    TestCase(
        id="L2.5",
        category=TestCategory.L2_JOIN,
        natural_language="显示每个帖子的所有标签",
        database="medium",
        expected_sql=(r"SELECT .* FROM posts .* JOIN .* post_hashtags .* " r"JOIN .* hashtags .*"),
        validation_rules=["has_join"],
        description="Many-to-many relationship",
    ),
    TestCase(
        id="L2.6",
        category=TestCategory.L2_JOIN,
        natural_language="显示价格超过 1000 的订单及客户邮箱",
        database="small",
        expected_sql=(
            r"SELECT .* FROM orders .* JOIN customers .* "
            r"ON .*customer_id.* WHERE .*total_amount\s*>\s*1000"
        ),
        validation_rules=["has_join", "has_where_clause"],
        description="Join with condition",
    ),
    TestCase(
        id="L2.7",
        category=TestCategory.L2_JOIN,
        natural_language="每个客户的总消费金额",
        database="small",
        expected_sql=(
            r"SELECT .* FROM customers .* LEFT JOIN orders .* "
            r"ON .*customer_id.* GROUP BY .* SUM\(.*total_amount.*\)"
        ),
        validation_rules=["has_join", "has_group_by", "uses_aggregate"],
        description="Aggregate with join",
    ),
    TestCase(
        id="L2.8",
        category=TestCategory.L2_JOIN,
        natural_language="显示产品统计信息",
        database="small",
        expected_sql=r"SELECT .* FROM product_stats",
        validation_rules=[],
        description="View query",
    ),
    TestCase(
        id="L2.9",
        category=TestCategory.L2_JOIN,
        natural_language="显示价格高于平均价的产品",
        database="small",
        expected_sql=(
            r"SELECT .* FROM products WHERE .* price\s*>\s*\("
            r"SELECT AVG\(price\) FROM products\)"
        ),
        validation_rules=["has_where_clause"],
        description="Scalar subquery",
    ),
    TestCase(
        id="L2.10",
        category=TestCategory.L2_JOIN,
        natural_language="显示有订单的客户",
        database="small",
        expected_sql=(
            r"(SELECT .* FROM customers WHERE customer_id IN \("
            r"SELECT customer_id FROM orders\)|"
            r"SELECT DISTINCT .* FROM customers .* "
            r"(INNER )?JOIN orders .* ON .*customer_id.*)"
        ),
        validation_rules=[],
        description="IN subquery or JOIN",
    ),
    TestCase(
        id="L2.11",
        category=TestCategory.L2_JOIN,
        natural_language="显示从未下单的客户",
        database="small",
        expected_sql=(
            r"(SELECT .* FROM customers WHERE customer_id NOT IN \("
            r"SELECT customer_id FROM orders\)|"
            r"SELECT .* FROM customers .* LEFT JOIN orders .* "
            r"ON .*customer_id.* WHERE .*order_id IS NULL)"
        ),
        validation_rules=[],
        description="NOT IN subquery or LEFT JOIN with NULL check",
    ),
    TestCase(
        id="L2.12",
        category=TestCategory.L2_JOIN,
        natural_language="显示有评论的产品",
        database="small",
        expected_sql=(
            r"SELECT .* FROM products .* WHERE EXISTS \("
            r"SELECT .* FROM reviews .* WHERE .*product_id.*\)"
        ),
        validation_rules=["has_where_clause"],
        description="EXISTS subquery",
    ),
    TestCase(
        id="L2.13",
        category=TestCategory.L2_JOIN,
        natural_language="显示所有产品和仓库的组合",
        database="large",
        expected_sql=r"SELECT .* FROM products .* CROSS JOIN .* warehouses",
        validation_rules=["has_join"],
        description="CROSS JOIN",
    ),
    TestCase(
        id="L2.14",
        category=TestCategory.L2_JOIN,
        natural_language="显示所有客户和供应商的邮箱",
        database="large",
        expected_sql=(r"SELECT email FROM customers UNION SELECT email FROM suppliers"),
        validation_rules=[],
        description="UNION",
    ),
    TestCase(
        id="L2.15",
        category=TestCategory.L2_JOIN,
        natural_language="显示每个订单的客户名字、产品名称和数量",
        database="small",
        expected_sql=(
            r"SELECT .* FROM orders .* JOIN customers .* "
            r"ON .*customer_id.* JOIN order_items .* ON .*order_id.* "
            r"JOIN products .* ON .*product_id.*"
        ),
        validation_rules=["has_join"],
        description="Complex four-table join",
    ),
]


# Pytest parametrize decorator for L2 tests
@pytest.mark.parametrize("test_case", L2_TEST_CASES, ids=lambda tc: tc.id)
@pytest.mark.asyncio
async def test_l2_join_queries(test_case: TestCase) -> None:
    """
    Test L2 multi-table join query generation.

    Args:
    ----------
        test_case: Test case definition

    Example:
    ----------
        >>> # Run with pytest
        >>> # pytest tests/contract/test_l2_join.py -v
    """
    # Test implementation will be added in test runner
    pytest.skip("Test case defined, runner not yet implemented")
