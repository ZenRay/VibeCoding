"""
Production integration example for SQL security validator.

This module demonstrates how to integrate the SQLValidator into a production
FastAPI application with proper logging, monitoring, and error handling.
"""

from typing import Any
import logging
from datetime import datetime
from functools import lru_cache

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from sql_validator import SQLValidator, ValidationResult


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Pydantic models
class QueryRequest(BaseModel):
    """Request model for SQL query execution."""

    sql: str = Field(..., description="SQL query to execute", min_length=1, max_length=50000)
    strip_comments: bool = Field(
        default=True,
        description="Whether to strip SQL comments before validation",
    )


class QueryResponse(BaseModel):
    """Response model for successful query execution."""

    data: list[dict[str, Any]]
    row_count: int
    execution_time_ms: float


class ErrorResponse(BaseModel):
    """Response model for validation errors."""

    error: str
    message: str
    error_type: str
    dangerous_elements: list[str] | None = None
    timestamp: str


# Security metrics (in production, use proper metrics system like Prometheus)
class SecurityMetrics:
    """Track security-related metrics."""

    def __init__(self):
        self.blocked_queries = 0
        self.validated_queries = 0
        self.validation_errors = 0
        self.blocked_by_type: dict[str, int] = {}

    def record_blocked(self, error_type: str):
        """Record a blocked query."""
        self.blocked_queries += 1
        self.blocked_by_type[error_type] = self.blocked_by_type.get(error_type, 0) + 1

    def record_validated(self):
        """Record a successfully validated query."""
        self.validated_queries += 1

    def record_error(self):
        """Record a validation error."""
        self.validation_errors += 1

    def get_stats(self) -> dict[str, Any]:
        """Get current metrics."""
        return {
            "total_validations": self.validated_queries + self.blocked_queries,
            "validated_queries": self.validated_queries,
            "blocked_queries": self.blocked_queries,
            "validation_errors": self.validation_errors,
            "blocked_by_type": self.blocked_by_type,
        }


# Initialize FastAPI app
app = FastAPI(
    title="Secure SQL Query API",
    description="SQL query API with comprehensive security validation",
    version="1.0.0",
)

# Initialize validator and metrics
validator = SQLValidator(dialect="postgres")
metrics = SecurityMetrics()


# Optional: Cached validator for repeated queries
class CachedSQLValidator(SQLValidator):
    """Validator with LRU cache for repeated queries."""

    @lru_cache(maxsize=1000)
    def validate(self, sql: str, strip_comments: bool = True) -> ValidationResult:
        """Cached validation - reuses results for identical queries."""
        return super().validate(sql, strip_comments)


# Use cached validator for better performance
cached_validator = CachedSQLValidator(dialect="postgres")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware to log all requests."""
    start_time = datetime.now()
    response = await call_next(request)
    duration = (datetime.now() - start_time).total_seconds() * 1000

    logger.info(
        "Request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration,
        },
    )

    return response


@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest) -> QueryResponse:
    """
    Execute SQL query with security validation.

    This endpoint:
    1. Validates the SQL query for security
    2. Blocks any non-SELECT statements
    3. Blocks dangerous functions
    4. Logs all blocked queries for security monitoring
    5. Executes safe queries and returns results

    Args:
        request: QueryRequest with SQL query

    Returns:
        QueryResponse with query results

    Raises:
        HTTPException: If query validation fails
    """
    # Validate SQL query
    result: ValidationResult = cached_validator.validate(
        request.sql,
        strip_comments=request.strip_comments,
    )

    if not result.is_valid:
        # Log security violation
        logger.warning(
            "Blocked unsafe SQL query",
            extra={
                "error_type": result.error_type,
                "error_message": result.error_message,
                "dangerous_elements": result.dangerous_elements,
                "query_preview": request.sql[:100],
            },
        )

        # Record metrics
        metrics.record_blocked(result.error_type or "UNKNOWN")

        # Return user-friendly error
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="Query validation failed",
                message=result.error_message or "Unknown validation error",
                error_type=result.error_type or "UNKNOWN",
                dangerous_elements=result.dangerous_elements,
                timestamp=datetime.now().isoformat(),
            ).model_dump(),
        )

    # Query passed validation
    metrics.record_validated()

    # Execute query (replace with actual database execution)
    try:
        query_result = await execute_safe_query(request.sql)
        return query_result
    except Exception as e:
        logger.error(f"Query execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "Query execution failed", "message": str(e)},
        )


async def execute_safe_query(sql: str) -> QueryResponse:
    """
    Execute validated SQL query against database.

    In production, replace this with actual database connection.

    Args:
        sql: Validated SQL query

    Returns:
        QueryResponse with results
    """
    # TODO: Replace with actual database execution
    # Example with asyncpg:
    #
    # import asyncpg
    # pool = await asyncpg.create_pool(
    #     host='localhost',
    #     database='mydb',
    #     user='myuser',
    #     password='mypassword'
    # )
    #
    # async with pool.acquire() as conn:
    #     start_time = datetime.now()
    #     rows = await conn.fetch(sql)
    #     execution_time = (datetime.now() - start_time).total_seconds() * 1000
    #
    #     return QueryResponse(
    #         data=[dict(row) for row in rows],
    #         row_count=len(rows),
    #         execution_time_ms=execution_time
    #     )

    # Mock response for demonstration
    return QueryResponse(
        data=[
            {"id": 1, "name": "User 1", "active": True},
            {"id": 2, "name": "User 2", "active": True},
        ],
        row_count=2,
        execution_time_ms=5.2,
    )


@app.get("/metrics")
async def get_metrics():
    """
    Get security metrics.

    Returns statistics about:
    - Total validations performed
    - Queries validated and allowed
    - Queries blocked
    - Validation errors
    - Breakdown by error type
    """
    return metrics.get_stats()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Example usage
if __name__ == "__main__":
    import uvicorn

    print("=" * 80)
    print("SECURE SQL QUERY API")
    print("=" * 80)
    print("\nStarting API server with SQL security validation...")
    print("\nEndpoints:")
    print("  POST /query - Execute SQL query")
    print("  GET /metrics - View security metrics")
    print("  GET /health - Health check")
    print("\nExample request:")
    print("""
    curl -X POST http://localhost:8000/query \\
      -H "Content-Type: application/json" \\
      -d '{"sql": "SELECT * FROM users"}'
    """)
    print("\nBlocked request example:")
    print("""
    curl -X POST http://localhost:8000/query \\
      -H "Content-Type: application/json" \\
      -d '{"sql": "DELETE FROM users"}'
    """)
    print("\n" + "=" * 80)

    uvicorn.run(app, host="0.0.0.0", port=8000)
