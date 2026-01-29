"""
FastAPI integration example for PoolManager.

Demonstrates how to use PoolManager in a production FastAPI application
with proper lifecycle management, error handling, and API endpoints.
"""

from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from pool_manager import DBConfig, PoolManager, PoolStats

# Global pool manager instance
pool_manager: PoolManager | None = None


class QueryRequest(BaseModel):
    """Request model for query execution."""

    query: str
    timeout: float = 30.0


class QueryResponse(BaseModel):
    """Response model for query execution."""

    rows: list[dict]
    count: int
    execution_time_ms: float


class DatabaseCreateResponse(BaseModel):
    """Response model for database creation."""

    db_id: str
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup (create pool manager and preconfigured pools)
    and shutdown (close all pools gracefully).
    """
    global pool_manager

    # Startup: Create pool manager and preconfigured pools
    pool_manager = PoolManager(
        idle_pool_timeout=timedelta(minutes=30),
        enable_monitoring=True,
        enable_cleanup=True,
    )

    # Load preconfigured databases from environment or config
    preconfigured = [
        DBConfig(
            host="localhost",
            port=5432,
            database="myapp",
            user="postgres",
            password="secret",
        ),
        DBConfig(
            host="analytics-db.example.com",
            port=5432,
            database="analytics",
            user="readonly",
            password="readonly",
            pool_min_size=10,  # Higher baseline for analytics
            pool_max_size=50,
        ),
    ]

    for config in preconfigured:
        try:
            await pool_manager.create_pool(config)
        except ConnectionError as e:
            # Log but don't fail startup if preconfigured DB is unavailable
            app.logger.error(f"Failed to create preconfigured pool: {e}")

    yield

    # Shutdown: Close all pools
    if pool_manager:
        await pool_manager.close_all()


# Create FastAPI app with lifespan
app = FastAPI(
    title="Multi-Database Query API",
    description="Execute SQL queries across multiple PostgreSQL databases",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "multi-database-query-api"}


@app.post(
    "/query/{db_id}",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Database not found"},
        403: {"description": "Permission denied"},
        408: {"description": "Query timeout"},
        503: {"description": "Database unavailable"},
    },
)
async def execute_query(db_id: str, request: QueryRequest):
    """
    Execute SQL query on specified database.

    Args:
        db_id: Database identifier (from connection creation)
        request: Query request with SQL and optional timeout

    Returns:
        Query results with row count and execution time

    Raises:
        HTTPException: Various status codes based on error type
    """
    import time

    start_time = time.time()

    try:
        result = await pool_manager.execute_query(
            db_id=db_id,
            query=request.query,
            timeout=request.timeout,
            readonly=True,
        )

        execution_time = (time.time() - start_time) * 1000  # Convert to ms

        return QueryResponse(
            rows=result,
            count=len(result),
            execution_time_ms=round(execution_time, 2),
        )

    except ValueError as e:
        # Pool not found or invalid SQL
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    except TimeoutError as e:
        raise HTTPException(status_code=408, detail=str(e))

    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post(
    "/databases",
    response_model=DatabaseCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        503: {"description": "Failed to connect to database"},
    },
)
async def create_database_connection(config: DBConfig):
    """
    Create new database connection pool.

    Args:
        config: Database connection configuration

    Returns:
        Database ID and creation status

    Raises:
        HTTPException: 503 if connection fails
    """
    try:
        db_id = await pool_manager.create_pool(config)
        return DatabaseCreateResponse(db_id=db_id, status="created")

    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to database: {e}",
        )


@app.get(
    "/databases/{db_id}/stats",
    response_model=PoolStats,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Database not found"},
    },
)
async def get_pool_stats(db_id: str):
    """
    Get connection pool statistics.

    Args:
        db_id: Database identifier

    Returns:
        Pool statistics including size, utilization, and performance metrics

    Raises:
        HTTPException: 404 if database not found
    """
    stats = await pool_manager.get_pool_stats(db_id)
    if stats is None:
        raise HTTPException(
            status_code=404,
            detail=f"Database {db_id} not found",
        )
    return stats


@app.post(
    "/databases/{db_id}/invalidate-cache",
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Database not found"},
    },
)
async def invalidate_cache(db_id: str):
    """
    Force schema cache invalidation for database.

    Useful after ALTER TABLE or other schema changes.

    Args:
        db_id: Database identifier

    Returns:
        Status message

    Raises:
        HTTPException: 404 if database not found
    """
    try:
        await pool_manager.invalidate_schema_cache(db_id)
        return {"status": "cache_invalidated", "db_id": db_id}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete(
    "/databases/{db_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def close_database_pool(db_id: str):
    """
    Close database connection pool.

    Args:
        db_id: Database identifier

    Returns:
        No content (204)
    """
    await pool_manager.close_pool(db_id)


@app.get("/databases")
async def list_databases():
    """
    List all active database pools with their statistics.

    Returns:
        List of database IDs and their statistics
    """
    databases = []
    for db_id in pool_manager._pools.keys():
        stats = await pool_manager.get_pool_stats(db_id)
        if stats:
            databases.append(stats)

    return {"databases": databases, "count": len(databases)}


# Run with: uvicorn fastapi_integration:app --reload
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
