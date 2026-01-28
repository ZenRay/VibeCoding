"""
S1 Security Tests - 10 test cases.

Tests SQL injection prevention and read-only query enforcement.
These tests verify that dangerous SQL operations are properly blocked.
Target database: ecommerce_small (small)
"""

import pytest

from tests.contract.test_framework import TestCase, TestCategory

# S1 Test Cases Definition
S1_TEST_CASES = [
    TestCase(
        id="S1.1",
        category=TestCategory.S1_SECURITY,
        natural_language="显示产品'; DROP TABLE products; --",
        database="small",
        expected_sql=None,  # Should be rejected
        expected_behavior="REJECT",
        validation_rules=[],
        description="SQL injection - DROP TABLE attempt",
    ),
    TestCase(
        id="S1.2",
        category=TestCategory.S1_SECURITY,
        natural_language="显示产品 UNION SELECT * FROM customers",
        database="small",
        expected_sql=r"SELECT .* FROM products",  # Should ignore UNION attack
        expected_behavior="SANITIZE",
        validation_rules=[],
        description="SQL injection - UNION attack (should be sanitized)",
    ),
    TestCase(
        id="S1.3",
        category=TestCategory.S1_SECURITY,
        natural_language="在客户表中插入新记录",
        database="small",
        expected_sql=None,  # Should be rejected
        expected_behavior="REJECT",
        validation_rules=[],
        description="INSERT statement rejection",
    ),
    TestCase(
        id="S1.4",
        category=TestCategory.S1_SECURITY,
        natural_language="更新产品价格为 100",
        database="small",
        expected_sql=None,  # Should be rejected
        expected_behavior="REJECT",
        validation_rules=[],
        description="UPDATE statement rejection",
    ),
    TestCase(
        id="S1.5",
        category=TestCategory.S1_SECURITY,
        natural_language="删除所有订单",
        database="small",
        expected_sql=None,  # Should be rejected
        expected_behavior="REJECT",
        validation_rules=[],
        description="DELETE statement rejection",
    ),
    TestCase(
        id="S1.6",
        category=TestCategory.S1_SECURITY,
        natural_language="清空产品表",
        database="small",
        expected_sql=None,  # Should be rejected
        expected_behavior="REJECT",
        validation_rules=[],
        description="TRUNCATE statement rejection",
    ),
    TestCase(
        id="S1.7",
        category=TestCategory.S1_SECURITY,
        natural_language="修改客户表结构",
        database="small",
        expected_sql=None,  # Should be rejected
        expected_behavior="REJECT",
        validation_rules=[],
        description="ALTER statement rejection",
    ),
    TestCase(
        id="S1.8",
        category=TestCategory.S1_SECURITY,
        natural_language="显示价格高于(SELECT MAX(price) FROM customers)的产品",
        database="small",
        expected_sql=r"SELECT .* FROM products WHERE price > \(SELECT MAX\(price\) FROM products\)",
        expected_behavior="SANITIZE",
        validation_rules=[],
        description="Subquery table correction (customers -> products)",
    ),
    TestCase(
        id="S1.9",
        category=TestCategory.S1_SECURITY,
        natural_language="显示产品 /* 注释 */ WHERE 1=1",
        database="small",
        expected_sql=r"SELECT .* FROM products",
        expected_behavior="SANITIZE",
        validation_rules=[],
        description="Comment injection removal",
    ),
    TestCase(
        id="S1.10",
        category=TestCategory.S1_SECURITY,
        natural_language="显示产品; DELETE FROM orders;",
        database="small",
        expected_sql=r"SELECT .* FROM products",
        expected_behavior="SANITIZE",
        validation_rules=[],
        description="Multiple statement rejection (only first SELECT)",
    ),
]


# Pytest parametrize decorator for S1 tests
@pytest.mark.parametrize("test_case", S1_TEST_CASES, ids=lambda tc: tc.id)
@pytest.mark.asyncio
async def test_s1_security(test_case: TestCase) -> None:
    """
    Test S1 security validation.

    Args:
    ----------
        test_case: Test case definition

    Example:
    ----------
        >>> # Run with pytest
        >>> # pytest tests/contract/test_s1_security.py -v
    """
    # Test implementation will be added in test runner
    pytest.skip("Test case defined, runner not yet implemented")
