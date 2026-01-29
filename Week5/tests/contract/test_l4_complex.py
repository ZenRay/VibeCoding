"""
L4 Complex Logic Tests - 10 test cases.

Tests complex business logic including recursive queries, JSON,
full-text search, and advanced SQL features.
Target databases: ecommerce_small (small), social_medium (medium),
erp_large (large)
"""

import pytest

from tests.contract.test_framework import TestCase, TestCategory

# L4 Test Cases Definition
L4_TEST_CASES = [
    TestCase(
        id="L4.1",
        category=TestCategory.L4_COMPLEX,
        natural_language="显示所有评论及其回复(包括嵌套回复)",
        database="social_medium",
        expected_sql=(
            r"WITH RECURSIVE .* AS \(SELECT .* FROM comments "
            r"WHERE parent_comment_id IS NULL UNION ALL SELECT .* "
            r"FROM comments .* JOIN .* ON .*parent_comment_id.*\)"
        ),
        validation_rules=[],
        description="Recursive CTE for hierarchical data",
    ),
    TestCase(
        id="L4.2",
        category=TestCategory.L4_COMPLEX,
        natural_language="显示元数据中包含 'click' 活动的用户行为",
        database="social_medium",
        expected_sql=(
            r"SELECT .* FROM user_activity WHERE "
            r"(metadata @> '.*click.*'|metadata->>'event_type' = 'click')"
        ),
        validation_rules=["has_where_clause"],
        description="JSONB query with operators",
    ),
    TestCase(
        id="L4.3",
        category=TestCategory.L4_COMPLEX,
        natural_language="显示注册后 7 天内下单的客户",
        database="ecommerce_small",
        expected_sql=(
            r"SELECT .* FROM customers .* JOIN orders .* "
            r"WHERE .*order_date.*<=.*created_at.*\+.*INTERVAL\s*'7\s*days?'"
        ),
        validation_rules=["has_join", "has_where_clause"],
        description="Complex time calculation",
    ),
    TestCase(
        id="L4.4",
        category=TestCategory.L4_COMPLEX,
        natural_language="搜索帖子内容包含 'database' 或 'sql' 的帖子",
        database="social_medium",
        expected_sql=(
            r"SELECT .* FROM posts WHERE "
            r"(to_tsvector.*@@.*to_tsquery|content\s+(ILIKE|LIKE).*database.*"
            r"(OR|ILIKE|LIKE).*sql)"
        ),
        validation_rules=["has_where_clause"],
        description="Full-text search or ILIKE",
    ),
    TestCase(
        id="L4.5",
        category=TestCategory.L4_COMPLEX,
        natural_language="根据价格区间给产品分类",
        database="ecommerce_small",
        expected_sql=(
            r"SELECT .* CASE\s+WHEN price.*<.*50.*THEN.*"
            r"WHEN price.*BETWEEN.*50.*AND.*200.*THEN.*"
            r"WHEN price.*>.*200.*THEN.*END.* FROM products"
        ),
        validation_rules=[],
        description="Complex CASE expression",
    ),
    TestCase(
        id="L4.6",
        category=TestCategory.L4_COMPLEX,
        natural_language="显示有超过 5 个标签的帖子",
        database="social_medium",
        expected_sql=(
            r"SELECT .* FROM posts .* JOIN .* post_hashtags .* "
            r"GROUP BY .* HAVING COUNT\(.*\)\s*>\s*5"
        ),
        validation_rules=["has_join", "has_group_by"],
        description="Array/many-to-many with HAVING",
    ),
    TestCase(
        id="L4.7",
        category=TestCategory.L4_COMPLEX,
        natural_language="显示每个产品及其在同类别中的价格排名",
        database="ecommerce_small",
        expected_sql=(
            r"SELECT .* \(SELECT COUNT\(\*\).* FROM products .* "
            r"WHERE .*category.*=.*category.* AND .*price.*>.*price.*\).* "
            r"FROM products"
        ),
        validation_rules=[],
        description="Correlated subquery for ranking",
    ),
    TestCase(
        id="L4.8",
        category=TestCategory.L4_COMPLEX,
        natural_language="显示既是客户又是供应商的邮箱",
        database="erp_large",
        expected_sql=r"SELECT email FROM customers INTERSECT SELECT email FROM suppliers",
        validation_rules=[],
        description="Set operation INTERSECT",
    ),
    TestCase(
        id="L4.9",
        category=TestCategory.L4_COMPLEX,
        natural_language="显示有产品但没有订单的类别",
        database="ecommerce_small",
        expected_sql=(
            r"SELECT DISTINCT category FROM products EXCEPT "
            r"SELECT DISTINCT .* FROM products .* JOIN order_items"
        ),
        validation_rules=[],
        description="Set operation EXCEPT",
    ),
    TestCase(
        id="L4.10",
        category=TestCategory.L4_COMPLEX,
        natural_language="显示每个部门的平均员工工资,只显示平均工资高于全公司平均工资的部门",
        database="erp_large",
        expected_sql=(
            r"SELECT .* FROM departments .* JOIN employees .* "
            r"GROUP BY .* HAVING AVG\(.*salary.*\)\s*>\s*"
            r"\(SELECT AVG\(salary\) FROM employees\)"
        ),
        validation_rules=["has_join", "has_group_by"],
        description="Multi-level aggregation with HAVING subquery",
    ),
]


# Pytest parametrize decorator for L4 tests
@pytest.mark.parametrize("test_case", L4_TEST_CASES, ids=lambda tc: tc.id)
@pytest.mark.asyncio
async def test_l4_complex_queries(test_case: TestCase) -> None:
    """
    Test L4 complex logic query generation.

    Args:
    ----------
        test_case: Test case definition

    Example:
    ----------
        >>> # Run with pytest
        >>> # pytest tests/contract/test_l4_complex.py -v
    """
    # Test implementation will be added in test runner
    pytest.skip("Test case defined, runner not yet implemented")
