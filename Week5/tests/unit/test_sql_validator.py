"""
Unit tests for SQL Validator.

Tests SQL safety validation using SQLGlot AST parsing.
"""

import pytest

from postgres_mcp.core.sql_validator import (
    SQLValidator,
)


@pytest.fixture
def sql_validator():
    """Create SQLValidator instance."""
    return SQLValidator()


# ============================================================================
# Basic SELECT Query Tests
# ============================================================================


def test_validate_simple_select(sql_validator):
    """Test simple SELECT query validation."""
    sql = "SELECT id, name FROM users LIMIT 100;"
    result = sql_validator.validate(sql)
    assert result.valid is True
    assert result.errors == []


def test_validate_select_with_where(sql_validator):
    """Test SELECT with WHERE clause."""
    sql = "SELECT * FROM users WHERE id = 123;"
    result = sql_validator.validate(sql)
    assert result.valid is True


def test_validate_select_with_join(sql_validator):
    """Test SELECT with JOIN."""
    sql = """
    SELECT u.id, u.name, o.total
    FROM users u
    INNER JOIN orders o ON u.id = o.user_id
    WHERE o.status = 'completed';
    """
    result = sql_validator.validate(sql)
    assert result.valid is True


def test_validate_select_with_limit(sql_validator):
    """Test SELECT with LIMIT."""
    sql = "SELECT * FROM users LIMIT 100;"
    result = sql_validator.validate(sql)
    assert result.valid is True


def test_validate_select_with_offset(sql_validator):
    """Test SELECT with OFFSET."""
    sql = "SELECT * FROM users LIMIT 100 OFFSET 50;"
    result = sql_validator.validate(sql)
    assert result.valid is True


# ============================================================================
# Aggregate and Group By Tests
# ============================================================================


def test_validate_count_aggregate(sql_validator):
    """Test COUNT aggregate function."""
    sql = "SELECT COUNT(*) FROM users;"
    result = sql_validator.validate(sql)
    assert result.valid is True


def test_validate_group_by(sql_validator):
    """Test GROUP BY clause."""
    sql = "SELECT category, COUNT(*) FROM products GROUP BY category;"
    result = sql_validator.validate(sql)
    assert result.valid is True


def test_validate_having_clause(sql_validator):
    """Test HAVING clause."""
    sql = """
    SELECT category, COUNT(*) as cnt
    FROM products
    GROUP BY category
    HAVING COUNT(*) > 5;
    """
    result = sql_validator.validate(sql)
    assert result.valid is True


# ============================================================================
# CTE (Common Table Expression) Tests
# ============================================================================


def test_validate_simple_cte(sql_validator):
    """Test simple CTE."""
    sql = """
    WITH active_users AS (
        SELECT * FROM users WHERE status = 'active'
    )
    SELECT * FROM active_users LIMIT 100;
    """
    result = sql_validator.validate(sql)
    assert result.valid is True


def test_validate_multiple_ctes(sql_validator):
    """Test multiple CTEs."""
    sql = """
    WITH active_users AS (
        SELECT * FROM users WHERE status = 'active'
    ),
    recent_orders AS (
        SELECT * FROM orders WHERE created_at > NOW() - INTERVAL '7 days'
    )
    SELECT u.*, o.total
    FROM active_users u
    LEFT JOIN recent_orders o ON u.id = o.user_id;
    """
    result = sql_validator.validate(sql)
    assert result.valid is True


# ============================================================================
# Subquery Tests
# ============================================================================


def test_validate_subquery_in_where(sql_validator):
    """Test subquery in WHERE clause."""
    sql = """
    SELECT * FROM users
    WHERE id IN (SELECT user_id FROM orders WHERE total > 1000);
    """
    result = sql_validator.validate(sql)
    assert result.valid is True


def test_validate_subquery_in_select(sql_validator):
    """Test subquery in SELECT clause."""
    sql = """
    SELECT
        id,
        name,
        (SELECT COUNT(*) FROM orders WHERE user_id = users.id) as order_count
    FROM users;
    """
    result = sql_validator.validate(sql)
    assert result.valid is True


# ============================================================================
# DML Statement Blocking Tests (DELETE, INSERT, UPDATE)
# ============================================================================


def test_block_delete_statement(sql_validator):
    """Test DELETE statement is blocked."""
    sql = "DELETE FROM users WHERE id = 1;"
    result = sql_validator.validate(sql)
    assert result.valid is False
    assert any("DELETE" in err.upper() for err in result.errors)


def test_block_insert_statement(sql_validator):
    """Test INSERT statement is blocked."""
    sql = "INSERT INTO users (name, email) VALUES ('test', 'test@example.com');"
    result = sql_validator.validate(sql)
    assert result.valid is False
    assert any("INSERT" in err.upper() for err in result.errors)


def test_block_update_statement(sql_validator):
    """Test UPDATE statement is blocked."""
    sql = "UPDATE users SET status = 'inactive' WHERE id = 1;"
    result = sql_validator.validate(sql)
    assert result.valid is False
    assert any("UPDATE" in err.upper() for err in result.errors)


# ============================================================================
# DDL Statement Blocking Tests (DROP, CREATE, ALTER)
# ============================================================================


def test_block_drop_table(sql_validator):
    """Test DROP TABLE is blocked."""
    sql = "DROP TABLE users;"
    result = sql_validator.validate(sql)
    assert result.valid is False
    assert any("DROP" in err.upper() for err in result.errors)


def test_block_create_table(sql_validator):
    """Test CREATE TABLE is blocked."""
    sql = "CREATE TABLE test (id INT, name TEXT);"
    result = sql_validator.validate(sql)
    assert result.valid is False
    assert any("CREATE" in err.upper() for err in result.errors)


def test_block_alter_table(sql_validator):
    """Test ALTER TABLE is blocked."""
    sql = "ALTER TABLE users ADD COLUMN status TEXT;"
    result = sql_validator.validate(sql)
    assert result.valid is False
    assert any("ALTER" in err.upper() for err in result.errors)


def test_block_truncate_table(sql_validator):
    """Test TRUNCATE is blocked."""
    sql = "TRUNCATE TABLE users;"
    result = sql_validator.validate(sql)
    assert result.valid is False
    assert any("TRUNCATE" in err.upper() for err in result.errors)


# ============================================================================
# Dangerous Function Blocking Tests
# ============================================================================


def test_block_pg_read_file(sql_validator):
    """Test pg_read_file() is blocked."""
    sql = "SELECT pg_read_file('/etc/passwd');"
    result = sql_validator.validate(sql)
    assert result.valid is False
    assert any("pg_read_file" in err for err in result.errors)


def test_block_pg_ls_dir(sql_validator):
    """Test pg_ls_dir() is blocked."""
    sql = "SELECT pg_ls_dir('/tmp');"
    result = sql_validator.validate(sql)
    assert result.valid is False


def test_block_copy_command(sql_validator):
    """Test COPY command is blocked."""
    sql = "COPY users TO '/tmp/users.csv';"
    result = sql_validator.validate(sql)
    assert result.valid is False
    assert any("COPY" in err.upper() for err in result.errors)


def test_allow_safe_functions(sql_validator):
    """Test safe functions are allowed."""
    sql = """
    SELECT
        NOW(),
        CURRENT_DATE,
        UPPER(name),
        LOWER(email),
        LENGTH(description)
    FROM users;
    """
    result = sql_validator.validate(sql)
    assert result.valid is True


# ============================================================================
# Comment Removal Tests
# ============================================================================


def test_remove_single_line_comments(sql_validator):
    """Test single-line comment removal."""
    sql = """
    SELECT id, name -- This is a comment
    FROM users;
    """
    result = sql_validator.validate(sql)
    assert result.valid is True


def test_remove_multi_line_comments(sql_validator):
    """Test multi-line comment removal."""
    sql = """
    SELECT id, name /* This is a
    multi-line comment */
    FROM users;
    """
    result = sql_validator.validate(sql)
    assert result.valid is True


def test_detect_comment_injection(sql_validator):
    """Test comment-based injection detection."""
    sql = "SELECT * FROM users WHERE id = 1 OR 1=1 --"
    # The validator should parse this correctly and allow it
    # (it's a valid SELECT, though the logic might be suspicious)
    result = sql_validator.validate(sql)
    # Should be valid syntactically, but might have warnings
    assert result.valid is True


# ============================================================================
# Injection Attack Tests
# ============================================================================


def test_block_union_injection(sql_validator):
    """Test UNION-based injection is blocked if not SELECT."""
    sql = "SELECT id FROM users WHERE id = 1 UNION SELECT password FROM admin_users;"
    # SQLGlot parses UNION as a Union node (not SELECT)
    result = sql_validator.validate(sql)
    # UNION is blocked because it's not a pure SELECT statement type
    assert result.valid is False
    assert any("Union" in err or "UNION" in err for err in result.errors)


def test_block_stacked_queries(sql_validator):
    """Test stacked query injection is blocked."""
    sql = "SELECT * FROM users; DROP TABLE users;"
    # SQLGlot will parse this as multiple statements
    result = sql_validator.validate(sql)
    assert result.valid is False
    assert any("multiple statements" in err.lower() for err in result.errors)


def test_block_time_based_injection(sql_validator):
    """Test time-based injection with pg_sleep."""
    sql = "SELECT * FROM users WHERE id = 1; SELECT pg_sleep(10);"
    result = sql_validator.validate(sql)
    assert result.valid is False


# ============================================================================
# Edge Cases and Malformed SQL
# ============================================================================


def test_empty_sql(sql_validator):
    """Test empty SQL validation."""
    result = sql_validator.validate("")
    assert result.valid is False
    assert any("empty" in err.lower() for err in result.errors)


def test_whitespace_only_sql(sql_validator):
    """Test whitespace-only SQL."""
    result = sql_validator.validate("   \n\t  ")
    assert result.valid is False


def test_invalid_syntax(sql_validator):
    """Test invalid SQL syntax."""
    sql = "SELECT * FROM WHERE;"
    result = sql_validator.validate(sql)
    assert result.valid is False
    assert any("syntax" in err.lower() or "parse" in err.lower() for err in result.errors)


def test_case_insensitive_keywords(sql_validator):
    """Test case-insensitive keyword detection."""
    sqls = [
        "delete from users;",
        "DELETE FROM users;",
        "DeLeTe FrOm users;",
    ]
    for sql in sqls:
        result = sql_validator.validate(sql)
        assert result.valid is False


# ============================================================================
# Warning Tests
# ============================================================================


def test_warn_select_star(sql_validator):
    """Test warning for SELECT *."""
    sql = "SELECT * FROM users;"
    result = sql_validator.validate(sql)
    assert result.valid is True
    # SELECT * should trigger a warning
    assert any("SELECT *" in warn or "wildcard" in warn.lower() for warn in result.warnings)


def test_warn_no_limit(sql_validator):
    """Test warning for missing LIMIT."""
    sql = "SELECT id, name FROM users;"
    result = sql_validator.validate(sql)
    assert result.valid is True
    # Missing LIMIT should trigger a warning
    assert any("LIMIT" in warn or "limit" in warn.lower() for warn in result.warnings)


def test_no_warn_with_limit(sql_validator):
    """Test no warning when LIMIT is present."""
    sql = "SELECT id, name FROM users LIMIT 100;"
    result = sql_validator.validate(sql)
    assert result.valid is True
    # Should not have LIMIT warning
    assert not any("limit" in warn.lower() for warn in result.warnings)


# ============================================================================
# Property-Based Tests (Hypothesis)
# ============================================================================


def test_always_block_write_operations(sql_validator):
    """Property: All write operations should be blocked."""
    dangerous_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE"]

    for keyword in dangerous_keywords:
        # Generate simple statement with keyword
        sql = f"{keyword} TABLE test;"
        result = sql_validator.validate(sql)
        assert result.valid is False, f"{keyword} should be blocked"


def test_always_allow_pure_select(sql_validator):
    """Property: Pure SELECT queries should always be allowed."""
    safe_selects = [
        "SELECT 1;",
        "SELECT NOW();",
        "SELECT * FROM users LIMIT 1;",
        "SELECT id, name FROM products WHERE active = true LIMIT 100;",
    ]

    for sql in safe_selects:
        result = sql_validator.validate(sql)
        assert result.valid is True, f"Safe SELECT should be allowed: {sql}"
