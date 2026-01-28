"""
SQL Validator implementation.

Validates SQL queries for security and safety using SQLGlot AST parsing.
"""

from dataclasses import dataclass, field

import sqlglot
import structlog
from sqlglot import exp

logger = structlog.get_logger(__name__)


class ValidationError(Exception):
    """SQL validation error."""

    pass


@dataclass
class ValidationResult:
    """
    SQL validation result.

    Attributes:
    ----------
        valid: Whether the SQL is valid and safe
        errors: List of validation errors
        warnings: List of validation warnings
        cleaned_sql: SQL with comments removed (optional)
    """

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    cleaned_sql: str | None = None


class SQLValidator:
    """
    SQL security validator using SQLGlot AST parsing.

    Validates SQL queries to ensure they are read-only SELECT statements
    and do not contain dangerous operations or functions.
    """

    # Dangerous functions that should be blocked
    DANGEROUS_FUNCTIONS = {
        "pg_read_file",
        "pg_read_binary_file",
        "pg_ls_dir",
        "pg_stat_file",
        "pg_execute",
        "pg_sleep",
        "lo_import",
        "lo_export",
        "dblink",
        "dblink_exec",
    }

    # Statement types that are allowed (only SELECT)
    ALLOWED_STATEMENTS = {exp.Select}

    # Statement types that are explicitly blocked (DML/DDL)
    BLOCKED_STATEMENTS = {
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Create,
        exp.Alter,
        exp.Command,  # Covers TRUNCATE, COPY, etc.
        exp.Merge,
    }

    def __init__(self):
        """Initialize SQL validator."""
        pass

    def validate(self, sql: str) -> ValidationResult:
        """
        Validate SQL query for security and safety.

        Args:
        ----------
            sql: SQL query to validate

        Returns:
        ----------
            ValidationResult with validation status and messages

        Example:
        ----------
            >>> validator = SQLValidator()
            >>> result = validator.validate("SELECT * FROM users;")
            >>> assert result.valid is True
        """
        errors: list[str] = []
        warnings: list[str] = []

        # Check for empty SQL
        if not sql or not sql.strip():
            errors.append("SQL query cannot be empty")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # Remove comments
        cleaned_sql = self._remove_comments(sql)

        # Parse SQL using SQLGlot
        try:
            statements = sqlglot.parse(cleaned_sql, dialect="postgres")
        except Exception as e:
            logger.error("sql_parse_error", error=str(e), sql=sql[:200])
            errors.append(f"SQL syntax error: {e}")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # Check if we have any statements
        if not statements:
            errors.append("No valid SQL statements found")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        # Check for multiple statements (stacked queries)
        if len(statements) > 1:
            errors.append("Multiple statements not allowed (potential SQL injection)")
            return ValidationResult(valid=False, errors=errors, warnings=warnings)

        statement = statements[0]

        # Validate statement type
        stmt_errors = self._validate_statement_type(statement)
        errors.extend(stmt_errors)

        # If statement type is invalid, return early
        if errors:
            return ValidationResult(
                valid=False, errors=errors, warnings=warnings, cleaned_sql=cleaned_sql
            )

        # Check for dangerous functions
        func_errors = self._check_dangerous_functions(statement)
        errors.extend(func_errors)

        # Generate warnings
        stmt_warnings = self._generate_warnings(statement)
        warnings.extend(stmt_warnings)

        # Validation passed if no errors
        valid = len(errors) == 0

        return ValidationResult(
            valid=valid, errors=errors, warnings=warnings, cleaned_sql=cleaned_sql
        )

    def _remove_comments(self, sql: str) -> str:
        """
        Remove SQL comments to prevent comment-based injection.

        Args:
        ----------
            sql: SQL with potential comments

        Returns:
        ----------
            SQL with comments removed
        """
        # SQLGlot handles comment removal during parsing
        # But we'll do basic cleanup first
        lines = []
        for line in sql.split("\n"):
            # Remove single-line comments
            if "--" in line:
                line = line[: line.index("--")]
            lines.append(line)

        sql_without_line_comments = "\n".join(lines)

        # Remove multi-line comments (/* ... */)
        import re

        sql_cleaned = re.sub(r"/\*.*?\*/", "", sql_without_line_comments, flags=re.DOTALL)

        return sql_cleaned

    def _validate_statement_type(self, statement: exp.Expression) -> list[str]:
        """
        Validate that the statement is an allowed type.

        Args:
        ----------
            statement: Parsed SQL statement

        Returns:
        ----------
            List of validation errors (empty if valid)
        """
        errors: list[str] = []

        # Check if statement is explicitly blocked
        for blocked_type in self.BLOCKED_STATEMENTS:
            if isinstance(statement, blocked_type):
                stmt_name = blocked_type.__name__.upper()
                errors.append(f"{stmt_name} statements are not allowed (read-only queries only)")
                return errors

        # Check if statement is allowed
        is_allowed = any(isinstance(statement, allowed) for allowed in self.ALLOWED_STATEMENTS)

        if not is_allowed:
            stmt_type = type(statement).__name__
            errors.append(
                f"Statement type '{stmt_type}' is not allowed (only SELECT queries permitted)"
            )

        return errors

    def _check_dangerous_functions(self, statement: exp.Expression) -> list[str]:
        """
        Recursively check for dangerous functions in the SQL AST.

        Args:
        ----------
            statement: Parsed SQL statement

        Returns:
        ----------
            List of validation errors for dangerous functions
        """
        errors: list[str] = []

        # Recursively traverse the AST
        for node in statement.walk():
            # Check for function calls
            if isinstance(node, exp.Anonymous) or isinstance(node, exp.Func):
                func_name = self._get_function_name(node)
                if func_name and func_name.lower() in self.DANGEROUS_FUNCTIONS:
                    errors.append(
                        f"Dangerous function '{func_name}' is not allowed (potential security risk)"
                    )

        return errors

    def _get_function_name(self, node: exp.Expression) -> str | None:
        """
        Extract function name from a function node.

        Args:
        ----------
            node: Function expression node

        Returns:
        ----------
            Function name or None
        """
        if isinstance(node, exp.Anonymous):
            return node.this if isinstance(node.this, str) else None
        elif isinstance(node, exp.Func):
            return node.sql_name()
        return None

    def _generate_warnings(self, statement: exp.Expression) -> list[str]:
        """
        Generate warnings for potentially problematic SQL patterns.

        Args:
        ----------
            statement: Parsed SQL statement

        Returns:
        ----------
            List of warning messages
        """
        warnings: list[str] = []

        # Check for SELECT *
        if isinstance(statement, exp.Select):
            for projection in statement.expressions:
                if isinstance(projection, exp.Star):
                    warnings.append(
                        "SELECT * detected: Consider specifying explicit columns "
                        "for better performance"
                    )
                    break

            # Check for missing LIMIT
            if not statement.args.get("limit"):
                warnings.append(
                    "No LIMIT clause detected: Consider adding LIMIT to prevent large result sets"
                )

        return warnings
