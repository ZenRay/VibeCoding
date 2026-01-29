"""
Comprehensive test suite for SQL security validator.

This module provides thorough testing of the SQLValidator class to ensure
100% blocking of non-SELECT statements while allowing safe queries.

Run tests with:
    pytest test_sql_validator.py -v
    pytest test_sql_validator.py -v --cov=sql_validator --cov-report=html
"""

import pytest
from sql_validator import SQLValidator, ValidationResult


class TestSQLValidatorBasicSelects:
    """Test valid SELECT statements."""

    @pytest.fixture
    def validator(self):
        """Create validator instance for tests."""
        return SQLValidator(dialect="postgres")

    def test_simple_select(self, validator):
        """Test basic SELECT statement."""
        result = validator.validate("SELECT * FROM users")
        assert result.is_valid
        assert result.error_message is None
        assert result.error_type is None

    def test_select_with_columns(self, validator):
        """Test SELECT with specific columns."""
        result = validator.validate("SELECT id, name, email FROM users")
        assert result.is_valid

    def test_select_with_where(self, validator):
        """Test SELECT with WHERE clause."""
        result = validator.validate("SELECT id, name FROM users WHERE active = true")
        assert result.is_valid

    def test_select_with_where_complex(self, validator):
        """Test SELECT with complex WHERE clause."""
        sql = """
            SELECT id, name, email
            FROM users
            WHERE active = true
              AND role IN ('admin', 'moderator')
              AND created_at > '2020-01-01'
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_select_with_order_by(self, validator):
        """Test SELECT with ORDER BY."""
        result = validator.validate("SELECT * FROM users ORDER BY name ASC, id DESC")
        assert result.is_valid

    def test_select_with_limit_offset(self, validator):
        """Test SELECT with LIMIT and OFFSET."""
        result = validator.validate("SELECT * FROM users LIMIT 10 OFFSET 20")
        assert result.is_valid

    def test_select_distinct(self, validator):
        """Test SELECT DISTINCT."""
        result = validator.validate("SELECT DISTINCT category FROM products")
        assert result.is_valid


class TestSQLValidatorJoins:
    """Test SELECT statements with JOINs."""

    @pytest.fixture
    def validator(self):
        return SQLValidator(dialect="postgres")

    def test_inner_join(self, validator):
        """Test SELECT with INNER JOIN."""
        sql = """
            SELECT u.id, u.name, o.order_id
            FROM users u
            INNER JOIN orders o ON u.id = o.user_id
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_left_join(self, validator):
        """Test SELECT with LEFT JOIN."""
        sql = """
            SELECT u.id, u.name, o.order_id
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_multiple_joins(self, validator):
        """Test SELECT with multiple JOINs."""
        sql = """
            SELECT u.id, u.name, o.order_id, p.product_name
            FROM users u
            INNER JOIN orders o ON u.id = o.user_id
            INNER JOIN order_items oi ON o.id = oi.order_id
            INNER JOIN products p ON oi.product_id = p.id
            WHERE u.active = true
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_self_join(self, validator):
        """Test SELECT with self-join."""
        sql = """
            SELECT e1.name as employee, e2.name as manager
            FROM employees e1
            LEFT JOIN employees e2 ON e1.manager_id = e2.id
        """
        result = validator.validate(sql)
        assert result.is_valid


class TestSQLValidatorSubqueries:
    """Test SELECT statements with subqueries."""

    @pytest.fixture
    def validator(self):
        return SQLValidator(dialect="postgres")

    def test_subquery_in_where(self, validator):
        """Test subquery in WHERE clause."""
        sql = """
            SELECT * FROM users
            WHERE id IN (
                SELECT user_id FROM orders WHERE total > 1000
            )
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_subquery_in_from(self, validator):
        """Test subquery in FROM clause."""
        sql = """
            SELECT sub.id, sub.name
            FROM (
                SELECT id, name FROM users WHERE active = true
            ) AS sub
            WHERE sub.name LIKE 'A%'
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_nested_subqueries(self, validator):
        """Test deeply nested subqueries."""
        sql = """
            SELECT * FROM (
                SELECT * FROM (
                    SELECT * FROM (
                        SELECT id, name FROM users
                    ) AS l3
                    WHERE id > 0
                ) AS l2
                WHERE name IS NOT NULL
            ) AS l1
            WHERE id < 1000
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_subquery_with_exists(self, validator):
        """Test subquery with EXISTS."""
        sql = """
            SELECT * FROM users u
            WHERE EXISTS (
                SELECT 1 FROM orders o
                WHERE o.user_id = u.id AND o.status = 'completed'
            )
        """
        result = validator.validate(sql)
        assert result.is_valid


class TestSQLValidatorCTEs:
    """Test SELECT statements with Common Table Expressions (CTEs)."""

    @pytest.fixture
    def validator(self):
        return SQLValidator(dialect="postgres")

    def test_simple_cte(self, validator):
        """Test simple CTE."""
        sql = """
            WITH active_users AS (
                SELECT id, name FROM users WHERE active = true
            )
            SELECT * FROM active_users
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_multiple_ctes(self, validator):
        """Test multiple CTEs."""
        sql = """
            WITH
                cte1 AS (SELECT id, name FROM users WHERE active = true),
                cte2 AS (SELECT user_id, SUM(total) as total FROM orders GROUP BY user_id),
                cte3 AS (
                    SELECT cte1.id, cte1.name, COALESCE(cte2.total, 0) as total_spent
                    FROM cte1
                    LEFT JOIN cte2 ON cte1.id = cte2.user_id
                )
            SELECT * FROM cte3 WHERE total_spent > 1000
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_recursive_cte(self, validator):
        """Test recursive CTE."""
        sql = """
            WITH RECURSIVE subordinates AS (
                SELECT id, name, manager_id FROM employees WHERE id = 1
                UNION ALL
                SELECT e.id, e.name, e.manager_id
                FROM employees e
                INNER JOIN subordinates s ON e.manager_id = s.id
            )
            SELECT * FROM subordinates
        """
        result = validator.validate(sql)
        assert result.is_valid


class TestSQLValidatorAggregates:
    """Test SELECT statements with aggregate functions."""

    @pytest.fixture
    def validator(self):
        return SQLValidator(dialect="postgres")

    def test_count(self, validator):
        """Test COUNT aggregate."""
        result = validator.validate("SELECT COUNT(*) FROM users")
        assert result.is_valid

    def test_multiple_aggregates(self, validator):
        """Test multiple aggregate functions."""
        sql = """
            SELECT
                category,
                COUNT(*) as count,
                AVG(price) as avg_price,
                MIN(price) as min_price,
                MAX(price) as max_price,
                SUM(quantity) as total_quantity
            FROM products
            GROUP BY category
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_having_clause(self, validator):
        """Test HAVING clause with aggregates."""
        sql = """
            SELECT category, COUNT(*) as count
            FROM products
            GROUP BY category
            HAVING COUNT(*) > 10
        """
        result = validator.validate(sql)
        assert result.is_valid


class TestSQLValidatorWindowFunctions:
    """Test SELECT statements with window functions."""

    @pytest.fixture
    def validator(self):
        return SQLValidator(dialect="postgres")

    def test_row_number(self, validator):
        """Test ROW_NUMBER() window function."""
        sql = """
            SELECT
                id,
                name,
                ROW_NUMBER() OVER (ORDER BY created_at DESC) as row_num
            FROM users
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_rank(self, validator):
        """Test RANK() window function."""
        sql = """
            SELECT
                id,
                name,
                salary,
                RANK() OVER (ORDER BY salary DESC) as salary_rank
            FROM employees
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_partition_by(self, validator):
        """Test window function with PARTITION BY."""
        sql = """
            SELECT
                id,
                department,
                salary,
                AVG(salary) OVER (PARTITION BY department) as dept_avg_salary
            FROM employees
        """
        result = validator.validate(sql)
        assert result.is_valid


class TestSQLValidatorSetOperations:
    """Test set operations (UNION, INTERSECT, EXCEPT)."""

    @pytest.fixture
    def validator(self):
        return SQLValidator(dialect="postgres")

    def test_union(self, validator):
        """Test UNION of SELECT statements."""
        sql = """
            SELECT id, name FROM customers
            UNION
            SELECT id, name FROM suppliers
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_union_all(self, validator):
        """Test UNION ALL."""
        sql = """
            SELECT id, name FROM customers
            UNION ALL
            SELECT id, name FROM suppliers
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_intersect(self, validator):
        """Test INTERSECT."""
        sql = """
            SELECT id FROM users WHERE active = true
            INTERSECT
            SELECT user_id FROM orders WHERE status = 'completed'
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_except(self, validator):
        """Test EXCEPT."""
        sql = """
            SELECT id FROM users
            EXCEPT
            SELECT user_id FROM banned_users
        """
        result = validator.validate(sql)
        assert result.is_valid


class TestSQLValidatorDMLBlocking:
    """Test that all DML operations are blocked."""

    @pytest.fixture
    def validator(self):
        return SQLValidator(dialect="postgres")

    def test_insert_blocked(self, validator):
        """Test that INSERT is blocked."""
        result = validator.validate("INSERT INTO users (name) VALUES ('hacker')")
        assert not result.is_valid
        assert result.error_type in ("FORBIDDEN_STATEMENT", "FORBIDDEN_OPERATION")
        assert "Insert" in result.error_message or "INSERT" in result.error_message.upper()

    def test_insert_select_blocked(self, validator):
        """Test that INSERT ... SELECT is blocked."""
        sql = """
            INSERT INTO archive_users
            SELECT * FROM users WHERE created_at < '2020-01-01'
        """
        result = validator.validate(sql)
        assert not result.is_valid

    def test_update_blocked(self, validator):
        """Test that UPDATE is blocked."""
        result = validator.validate("UPDATE users SET admin = true WHERE id = 1")
        assert not result.is_valid
        assert "Update" in result.error_message or "UPDATE" in result.error_message.upper()

    def test_update_from_blocked(self, validator):
        """Test that UPDATE ... FROM is blocked."""
        sql = """
            UPDATE users u
            SET status = 'inactive'
            FROM orders o
            WHERE u.id = o.user_id AND o.created_at < '2020-01-01'
        """
        result = validator.validate(sql)
        assert not result.is_valid

    def test_delete_blocked(self, validator):
        """Test that DELETE is blocked."""
        result = validator.validate("DELETE FROM users WHERE id = 1")
        assert not result.is_valid
        assert "Delete" in result.error_message or "DELETE" in result.error_message.upper()

    def test_delete_using_blocked(self, validator):
        """Test that DELETE ... USING is blocked."""
        sql = """
            DELETE FROM users u
            USING orders o
            WHERE u.id = o.user_id AND o.status = 'fraud'
        """
        result = validator.validate(sql)
        assert not result.is_valid


class TestSQLValidatorDDLBlocking:
    """Test that all DDL operations are blocked."""

    @pytest.fixture
    def validator(self):
        return SQLValidator(dialect="postgres")

    def test_create_table_blocked(self, validator):
        """Test that CREATE TABLE is blocked."""
        result = validator.validate("CREATE TABLE evil (id INT, data TEXT)")
        assert not result.is_valid
        assert result.error_type in ("FORBIDDEN_STATEMENT", "FORBIDDEN_OPERATION")

    def test_create_index_blocked(self, validator):
        """Test that CREATE INDEX is blocked."""
        result = validator.validate("CREATE INDEX idx_users_name ON users(name)")
        assert not result.is_valid

    def test_drop_table_blocked(self, validator):
        """Test that DROP TABLE is blocked."""
        result = validator.validate("DROP TABLE users")
        assert not result.is_valid

    def test_drop_index_blocked(self, validator):
        """Test that DROP INDEX is blocked."""
        result = validator.validate("DROP INDEX idx_users_name")
        assert not result.is_valid

    def test_alter_table_add_column_blocked(self, validator):
        """Test that ALTER TABLE ADD COLUMN is blocked."""
        result = validator.validate("ALTER TABLE users ADD COLUMN evil TEXT")
        assert not result.is_valid

    def test_alter_table_drop_column_blocked(self, validator):
        """Test that ALTER TABLE DROP COLUMN is blocked."""
        result = validator.validate("ALTER TABLE users DROP COLUMN name")
        assert not result.is_valid

    def test_truncate_blocked(self, validator):
        """Test that TRUNCATE is blocked."""
        result = validator.validate("TRUNCATE TABLE users")
        assert not result.is_valid


class TestSQLValidatorDangerousFunctions:
    """Test that dangerous PostgreSQL functions are blocked."""

    @pytest.fixture
    def validator(self):
        return SQLValidator(dialect="postgres")

    def test_pg_read_file_blocked(self, validator):
        """Test that pg_read_file is blocked."""
        result = validator.validate("SELECT pg_read_file('/etc/passwd')")
        assert not result.is_valid
        assert result.error_type == "DANGEROUS_FUNCTION"
        assert "pg_read_file" in result.dangerous_elements

    def test_pg_read_binary_file_blocked(self, validator):
        """Test that pg_read_binary_file is blocked."""
        result = validator.validate("SELECT pg_read_binary_file('/etc/shadow')")
        assert not result.is_valid
        assert "pg_read_binary_file" in result.dangerous_elements

    def test_pg_ls_dir_blocked(self, validator):
        """Test that pg_ls_dir is blocked."""
        result = validator.validate("SELECT pg_ls_dir('/etc')")
        assert not result.is_valid
        assert "pg_ls_dir" in result.dangerous_elements

    def test_pg_stat_file_blocked(self, validator):
        """Test that pg_stat_file is blocked."""
        result = validator.validate("SELECT pg_stat_file('/etc/passwd')")
        assert not result.is_valid

    def test_pg_terminate_backend_blocked(self, validator):
        """Test that pg_terminate_backend is blocked."""
        sql = """
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE usename = 'victim'
        """
        result = validator.validate(sql)
        assert not result.is_valid
        assert "pg_terminate_backend" in result.dangerous_elements

    def test_pg_cancel_backend_blocked(self, validator):
        """Test that pg_cancel_backend is blocked."""
        result = validator.validate("SELECT pg_cancel_backend(12345)")
        assert not result.is_valid

    def test_dangerous_function_in_where_blocked(self, validator):
        """Test dangerous function in WHERE clause is blocked."""
        sql = """
            SELECT * FROM users
            WHERE pg_read_file('/etc/passwd') IS NOT NULL
        """
        result = validator.validate(sql)
        assert not result.is_valid


class TestSQLValidatorNestedAttacks:
    """Test that attacks hidden in nested queries are detected."""

    @pytest.fixture
    def validator(self):
        return SQLValidator(dialect="postgres")

    def test_insert_in_subquery_blocked(self, validator):
        """Test that INSERT in subquery is blocked."""
        sql = """
            SELECT * FROM (
                INSERT INTO logs (message) VALUES ('hacked') RETURNING *
            ) AS fake_select
        """
        result = validator.validate(sql)
        assert not result.is_valid
        assert result.error_type == "FORBIDDEN_OPERATION"

    def test_delete_in_cte_blocked(self, validator):
        """Test that DELETE in CTE is blocked."""
        sql = """
            WITH deleted AS (
                DELETE FROM users WHERE id = 1 RETURNING *
            )
            SELECT * FROM deleted
        """
        result = validator.validate(sql)
        assert not result.is_valid

    def test_update_in_nested_cte_blocked(self, validator):
        """Test that UPDATE in nested CTE is blocked."""
        sql = """
            WITH cte1 AS (
                SELECT id FROM users
            ),
            cte2 AS (
                UPDATE users SET admin = true WHERE id IN (SELECT id FROM cte1) RETURNING *
            )
            SELECT * FROM cte2
        """
        result = validator.validate(sql)
        assert not result.is_valid

    def test_dangerous_function_in_subquery_blocked(self, validator):
        """Test that dangerous function in subquery is blocked."""
        sql = """
            SELECT * FROM users
            WHERE id IN (
                SELECT user_id FROM sessions
                WHERE data = pg_read_file('/etc/passwd')
            )
        """
        result = validator.validate(sql)
        assert not result.is_valid
        assert result.error_type == "DANGEROUS_FUNCTION"


class TestSQLValidatorCommentHandling:
    """Test SQL comment removal and validation."""

    @pytest.fixture
    def validator(self):
        return SQLValidator(dialect="postgres")

    def test_single_line_comment(self, validator):
        """Test single-line comment removal."""
        sql = "SELECT * FROM users -- This is a comment"
        result = validator.validate(sql)
        assert result.is_valid

    def test_multi_line_comment(self, validator):
        """Test multi-line comment removal."""
        sql = """
            SELECT * FROM users
            /* This is a
               multi-line comment */
            WHERE active = true
        """
        result = validator.validate(sql)
        assert result.is_valid

    def test_comment_hiding_attack(self, validator):
        """Test that attacks hidden in comments are neutralized."""
        sql = "SELECT * FROM users -- ; DELETE FROM users WHERE 1=1;"
        result = validator.validate(sql)
        # Should be valid after comment removal
        assert result.is_valid

    def test_comment_with_forbidden_keyword(self, validator):
        """Test that forbidden keywords in comments don't trigger false positive."""
        sql = "SELECT * FROM users -- This comment mentions DROP TABLE but it's safe"
        result = validator.validate(sql)
        assert result.is_valid

    def test_inline_comment(self, validator):
        """Test inline comments."""
        sql = "SELECT id, /* user name */ name FROM users"
        result = validator.validate(sql)
        assert result.is_valid


class TestSQLValidatorEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def validator(self):
        return SQLValidator(dialect="postgres")

    def test_empty_query(self, validator):
        """Test empty query string."""
        result = validator.validate("")
        assert not result.is_valid
        assert result.error_type == "SYNTAX_ERROR"

    def test_whitespace_only_query(self, validator):
        """Test query with only whitespace."""
        result = validator.validate("   \n\t   ")
        assert not result.is_valid
        assert result.error_type == "SYNTAX_ERROR"

    def test_invalid_syntax(self, validator):
        """Test query with invalid SQL syntax."""
        result = validator.validate("SELECT FROM WHERE")
        assert not result.is_valid
        assert result.error_type == "SYNTAX_ERROR"

    def test_unclosed_parenthesis(self, validator):
        """Test query with unclosed parenthesis."""
        result = validator.validate("SELECT * FROM (SELECT id FROM users")
        assert not result.is_valid

    def test_unclosed_string(self, validator):
        """Test query with unclosed string literal."""
        result = validator.validate("SELECT * FROM users WHERE name = 'unclosed")
        assert not result.is_valid

    def test_very_long_query(self, validator):
        """Test validation performance with long query."""
        # Generate a long but valid query
        columns = ", ".join([f"col{i}" for i in range(100)])
        sql = f"SELECT {columns} FROM users"
        result = validator.validate(sql)
        assert result.is_valid

    def test_deeply_nested_query(self, validator):
        """Test deeply nested subqueries."""
        # Build 10 levels of nesting
        sql = "SELECT * FROM users"
        for i in range(10):
            sql = f"SELECT * FROM ({sql}) AS level{i}"

        result = validator.validate(sql)
        assert result.is_valid


class TestSQLValidatorMultipleDialects:
    """Test validator with different SQL dialects."""

    def test_mysql_dialect(self):
        """Test validator with MySQL dialect."""
        validator = SQLValidator(dialect="mysql")
        result = validator.validate("SELECT * FROM users")
        assert result.is_valid

    def test_sqlite_dialect(self):
        """Test validator with SQLite dialect."""
        validator = SQLValidator(dialect="sqlite")
        result = validator.validate("SELECT * FROM users")
        assert result.is_valid

    def test_dialect_specific_syntax(self):
        """Test that dialect-specific syntax is handled."""
        # PostgreSQL specific: ILIKE operator
        validator = SQLValidator(dialect="postgres")
        result = validator.validate("SELECT * FROM users WHERE name ILIKE '%john%'")
        assert result.is_valid


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
