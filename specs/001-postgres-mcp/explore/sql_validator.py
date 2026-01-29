"""
SQL Security Validator using SQLGlot.

This module provides comprehensive SQL validation to ensure only safe SELECT
statements are executed, blocking all DML/DDL operations and dangerous functions.

Usage:
    validator = SQLValidator(dialect="postgres")
    result = validator.validate("SELECT * FROM users")
    if result.is_valid:
        # Execute query
        pass
    else:
        # Block query and log violation
        print(f"Blocked: {result.error_message}")
"""

from typing import NamedTuple
import re

try:
    import sqlglot
    from sqlglot import exp
except ImportError as e:
    raise ImportError(
        "SQLGlot is required for SQL validation. Install with: uv pip install sqlglot>=25.29"
    ) from e


class ValidationResult(NamedTuple):
    """
    Result of SQL validation.

    Attributes:
        is_valid: Whether the query passed validation
        error_message: Human-readable error description (None if valid)
        error_type: Error category for logging/monitoring (None if valid)
        dangerous_elements: List of specific dangerous elements found (None if valid)
    """

    is_valid: bool
    error_message: str | None = None
    error_type: str | None = None
    dangerous_elements: list[str] | None = None


class SQLValidator:
    """
    Secure SQL validator that allows only SELECT statements.

    This validator uses SQLGlot to parse SQL into an Abstract Syntax Tree (AST)
    and recursively validates all nodes to ensure:
    - Only SELECT statements at root level
    - No DML operations (INSERT, UPDATE, DELETE, MERGE)
    - No DDL operations (CREATE, ALTER, DROP, TRUNCATE)
    - No dangerous function calls (pg_read_file, etc.)
    - No dangerous operations in nested queries/CTEs

    Security Approach:
        1. Strip SQL comments to prevent comment-hiding attacks
        2. Parse SQL into AST using SQLGlot
        3. Validate root statement type
        4. Recursively traverse all nodes checking for forbidden types
        5. Check all function calls against blacklist

    Example:
        >>> validator = SQLValidator(dialect="postgres")
        >>> result = validator.validate("SELECT * FROM users")
        >>> print(result.is_valid)  # True
        >>>
        >>> result = validator.validate("DELETE FROM users")
        >>> print(result.is_valid)  # False
        >>> print(result.error_message)  # "Statement type not allowed: Delete..."
    """

    # Forbidden expression types - these represent SQL operations that modify data
    FORBIDDEN_TYPES = (
        # Data Manipulation Language (DML) - modifies data
        exp.Insert,  # INSERT INTO ...
        exp.Update,  # UPDATE ... SET ...
        exp.Delete,  # DELETE FROM ...
        exp.Merge,  # MERGE INTO ...
        # Data Definition Language (DDL) - modifies schema
        exp.Create,  # CREATE TABLE/INDEX/VIEW/...
        exp.Alter,  # ALTER TABLE/INDEX/...
        exp.Drop,  # DROP TABLE/INDEX/...
        exp.Truncate,  # TRUNCATE TABLE ...
        # Database commands
        exp.Command,  # Various database commands
        exp.Load,  # LOAD extension/file
        exp.Use,  # USE database
        exp.Set,  # SET variable = value
        # PostgreSQL-specific dangerous operations
        exp.Copy,  # COPY ... TO/FROM (can execute programs)
        # Transaction control that could be abused
        exp.Commit,  # COMMIT (in some contexts)
        exp.Rollback,  # ROLLBACK (in some contexts)
    )

    # Dangerous PostgreSQL functions that provide system access
    # Reference: https://www.postgresql.org/docs/current/functions-admin.html
    DANGEROUS_FUNCTIONS = frozenset(
        {
            # File system access functions
            "pg_read_file",  # Read arbitrary files on server
            "pg_read_binary_file",  # Read binary files
            "pg_ls_dir",  # List directory contents
            "pg_stat_file",  # Get file metadata
            # Administrative functions
            "pg_reload_conf",  # Reload PostgreSQL configuration
            "pg_rotate_logfile",  # Rotate server log files
            "pg_terminate_backend",  # Kill database connections
            "pg_cancel_backend",  # Cancel running queries
            "pg_switch_wal",  # WAL file management
            # Extension and language loading
            "load_extension",  # Load custom extensions
            # Untrusted procedural languages (can execute arbitrary code)
            "plpython3u",  # Untrusted Python
            "plperlu",  # Untrusted Perl
            "plpythonu",  # Legacy untrusted Python
            # Functions that can be used for SQL injection
            "pg_read_server_files",  # Read server files role
            "pg_write_server_files",  # Write server files role
            "pg_execute_server_program",  # Execute programs role
        }
    )

    def __init__(self, dialect: str = "postgres"):
        """
        Initialize SQL validator.

        Args:
            dialect: SQL dialect to use for parsing (default: "postgres")
                    Supported dialects: postgres, mysql, sqlite, etc.
        """
        self.dialect = dialect

    def validate(self, sql: str, strip_comments: bool = True) -> ValidationResult:
        """
        Validate SQL query for security compliance.

        This method performs comprehensive validation including:
        1. Comment removal (if enabled)
        2. SQL parsing
        3. Root statement type validation
        4. Recursive tree traversal for forbidden operations
        5. Dangerous function detection

        Args:
            sql: SQL query string to validate
            strip_comments: Whether to remove SQL comments before validation
                           (recommended: True to prevent comment-hiding attacks)

        Returns:
            ValidationResult containing:
                - is_valid: True if query passes all checks
                - error_message: Description of validation failure (if any)
                - error_type: Category of error for logging
                - dangerous_elements: List of specific violations found

        Examples:
            >>> validator = SQLValidator()
            >>> validator.validate("SELECT * FROM users").is_valid
            True
            >>> result = validator.validate("DROP TABLE users")
            >>> result.is_valid
            False
            >>> result.error_type
            'FORBIDDEN_STATEMENT'
        """
        # Step 1: Strip comments if requested (security best practice)
        if strip_comments:
            try:
                sql = self._strip_comments(sql)
            except Exception as e:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Failed to parse SQL for comment removal: {e}",
                    error_type="PARSE_ERROR",
                )

        # Step 2: Parse SQL into Abstract Syntax Tree
        try:
            parsed = sqlglot.parse_one(sql, read=self.dialect)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error_message=f"SQL syntax error: {e}",
                error_type="SYNTAX_ERROR",
            )

        # Step 3: Validate root statement type (must be SELECT or set operation)
        if not self._is_allowed_root_type(parsed):
            return ValidationResult(
                is_valid=False,
                error_message=(
                    f"Statement type not allowed: {type(parsed).__name__}. "
                    "Only SELECT queries are permitted."
                ),
                error_type="FORBIDDEN_STATEMENT",
            )

        # Step 4: Recursively check all nodes in the AST for forbidden operations
        forbidden = self._find_forbidden_expressions(parsed)
        if forbidden:
            return ValidationResult(
                is_valid=False,
                error_message=f"Query contains forbidden operations: {', '.join(forbidden)}",
                error_type="FORBIDDEN_OPERATION",
                dangerous_elements=forbidden,
            )

        # Step 5: Check all function calls against dangerous function blacklist
        dangerous_funcs = self._find_dangerous_functions(parsed)
        if dangerous_funcs:
            return ValidationResult(
                is_valid=False,
                error_message=f"Query contains dangerous functions: {', '.join(dangerous_funcs)}",
                error_type="DANGEROUS_FUNCTION",
                dangerous_elements=dangerous_funcs,
            )

        # All validation checks passed
        return ValidationResult(is_valid=True)

    def _strip_comments(self, sql: str) -> str:
        """
        Remove SQL comments from query string.

        Uses SQLGlot to parse and regenerate SQL without comments. This is more
        reliable than regex for handling complex cases like:
        - Comments within string literals
        - Nested comments (PostgreSQL)
        - Mixed comment types

        Falls back to regex-based removal if SQLGlot parsing fails.

        Args:
            sql: SQL query with comments

        Returns:
            SQL query with comments removed

        Note:
            SQLGlot's comment removal is "best effort" - some edge cases may
            not be fully handled. For critical security, consider additional
            validation layers.
        """
        try:
            # Parse and regenerate without comments
            parsed = sqlglot.parse_one(sql, read=self.dialect)
            return parsed.sql(dialect=self.dialect, comments=False, pretty=False)
        except Exception:
            # Fallback to regex-based comment removal
            return self._regex_remove_comments(sql)

    def _regex_remove_comments(self, sql: str) -> str:
        """
        Fallback regex-based comment removal.

        Handles:
        - Single-line comments: -- comment
        - Multi-line comments: /* comment */

        Limitations:
        - Does not handle nested comments (PostgreSQL feature)
        - May incorrectly remove comment-like text in string literals

        Args:
            sql: SQL query string

        Returns:
            SQL with comments removed
        """
        # Remove single-line comments (-- to end of line)
        sql = re.sub(r"--[^\n]*", "", sql)
        # Remove multi-line comments (/* ... */)
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
        return sql

    def _is_allowed_root_type(self, parsed: exp.Expression) -> bool:
        """
        Check if root statement type is allowed.

        Permitted root types:
        - SELECT: Standard select queries
        - UNION: Combining multiple select results
        - INTERSECT: Common rows between selects
        - EXCEPT: Rows in first select but not in second

        Args:
            parsed: Parsed SQL AST root node

        Returns:
            True if root type is allowed, False otherwise
        """
        return isinstance(
            parsed,
            (
                exp.Select,
                exp.Union,
                exp.Intersect,
                exp.Except,
            ),
        )

    def _find_forbidden_expressions(self, parsed: exp.Expression) -> list[str]:
        """
        Find all forbidden expression types in the query AST.

        Recursively traverses the entire AST tree to detect forbidden operations
        even when deeply nested (e.g., in subqueries, CTEs, etc.).

        Args:
            parsed: Root node of parsed SQL AST

        Returns:
            List of forbidden expression type names found (empty if none)

        Example:
            >>> # For: SELECT * FROM (INSERT INTO t VALUES (1) RETURNING *)
            >>> # Returns: ["Insert"]
        """
        forbidden = []

        for node in parsed.walk():
            if isinstance(node, self.FORBIDDEN_TYPES):
                expr_type = type(node).__name__
                if expr_type not in forbidden:
                    forbidden.append(expr_type)

        return forbidden

    def _find_dangerous_functions(self, parsed: exp.Expression) -> list[str]:
        """
        Find all dangerous function calls in the query.

        Checks all function call nodes in the AST against the dangerous function
        blacklist. Dangerous functions include those that:
        - Access the file system
        - Execute system commands
        - Modify database configuration
        - Terminate connections
        - Load untrusted code

        Args:
            parsed: Root node of parsed SQL AST

        Returns:
            List of dangerous function names found (empty if none)

        Example:
            >>> # For: SELECT pg_read_file('/etc/passwd')
            >>> # Returns: ["pg_read_file"]
        """
        dangerous = []

        for node in parsed.walk():
            # Check both generic function calls and specific function types
            if isinstance(node, (exp.Anonymous, exp.Func)):
                # Extract function name
                if isinstance(node, exp.Anonymous):
                    # Anonymous function call (generic)
                    func_name = str(node.this).lower() if node.this else ""
                elif hasattr(node, "sql_name"):
                    # Named function with sql_name method
                    func_name = node.sql_name().lower()
                else:
                    # Fallback: convert node to string and extract name
                    func_name = str(node).split("(")[0].lower()

                # Check against blacklist
                if func_name in self.DANGEROUS_FUNCTIONS:
                    if func_name not in dangerous:
                        dangerous.append(func_name)

        return dangerous


# Example usage and demonstration
if __name__ == "__main__":
    # Initialize validator
    validator = SQLValidator(dialect="postgres")

    # Test cases: (SQL query, expected_valid)
    test_queries = [
        # ===== VALID QUERIES =====
        ("SELECT * FROM users", True),
        ("SELECT id, name FROM users WHERE active = true", True),
        ("SELECT * FROM (SELECT id FROM users) AS sub", True),
        ("WITH cte AS (SELECT id FROM users) SELECT * FROM cte", True),
        (
            """
            SELECT u.id, u.name, o.order_id
            FROM users u
            INNER JOIN orders o ON u.id = o.user_id
            """,
            True,
        ),
        ("SELECT id FROM customers UNION SELECT id FROM suppliers", True),
        ("SELECT COUNT(*), AVG(price) FROM products GROUP BY category", True),
        # ===== INVALID - DML =====
        ("INSERT INTO users (name) VALUES ('hacker')", False),
        ("UPDATE users SET admin = true WHERE id = 1", False),
        ("DELETE FROM users WHERE id = 1", False),
        ("MERGE INTO target USING source ON target.id = source.id WHEN MATCHED THEN UPDATE SET value = 1", False),
        # ===== INVALID - DDL =====
        ("DROP TABLE users", False),
        ("CREATE TABLE evil (data text)", False),
        ("ALTER TABLE users ADD COLUMN evil text", False),
        ("TRUNCATE TABLE users", False),
        # ===== INVALID - DANGEROUS FUNCTIONS =====
        ("SELECT pg_read_file('/etc/passwd')", False),
        ("SELECT * FROM users WHERE pg_terminate_backend(123)", False),
        ("SELECT pg_ls_dir('/etc')", False),
        # ===== INVALID - NESTED ATTACKS =====
        ("SELECT * FROM (INSERT INTO logs VALUES ('x') RETURNING *) AS t", False),
        ("WITH cte AS (DELETE FROM users RETURNING *) SELECT * FROM cte", False),
        # ===== COMMENT HANDLING =====
        ("SELECT * FROM users -- ; DELETE FROM users WHERE 1=1;", True),  # Comment is stripped
        ("SELECT /* comment */ * FROM users", True),
    ]

    # Run tests
    print("=" * 70)
    print("SQL SECURITY VALIDATION TEST SUITE")
    print("=" * 70)

    passed = 0
    failed = 0

    for sql, expected_valid in test_queries:
        result = validator.validate(sql)
        status = "✓ PASS" if result.is_valid == expected_valid else "✗ FAIL"

        if result.is_valid == expected_valid:
            passed += 1
        else:
            failed += 1

        # Display first 60 chars of SQL
        sql_display = sql.strip().replace("\n", " ")[:60]
        if len(sql.strip()) > 60:
            sql_display += "..."

        print(f"\n{status}")
        print(f"SQL: {sql_display}")
        print(f"Result: Valid={result.is_valid} (Expected={expected_valid})")

        if not result.is_valid:
            print(f"Error Type: {result.error_type}")
            print(f"Message: {result.error_message}")
            if result.dangerous_elements:
                print(f"Dangerous Elements: {', '.join(result.dangerous_elements)}")

    # Summary
    print("\n" + "=" * 70)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 70)
