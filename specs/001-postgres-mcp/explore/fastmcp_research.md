# FastMCP 0.3+ Best Practices and Implementation Patterns

**Research Date**: 2026-01-28
**Target Use Case**: PostgreSQL MCP Server with asyncpg
**FastMCP Version**: 0.3+ (3.0.0b1 available, 2.x stable)

---

## Table of Contents

1. [Tools Definition Patterns](#1-tools-definition-patterns)
2. [Resources Exposure](#2-resources-exposure)
3. [Context Management](#3-context-management)
4. [Integration with Asyncpg](#4-integration-with-asyncpg)
5. [Architecture Patterns](#5-architecture-patterns)
6. [Common Pitfalls and Troubleshooting](#6-common-pitfalls-and-troubleshooting)

---

## 1. Tools Definition Patterns

### 1.1 Basic Tool Definition with Pydantic

**Decision**: Use Pydantic models for complex inputs with automatic validation.

**Pattern**:

```python
from fastmcp import FastMCP, Context
from pydantic import BaseModel, Field
from typing import Optional

mcp = FastMCP("postgres-mcp", version="1.0.0")

class QueryParams(BaseModel):
    """Parameters for executing a database query."""
    sql: str = Field(..., description="SQL query to execute")
    params: Optional[list] = Field(default=None, description="Query parameters")
    timeout: float = Field(default=30.0, ge=0, description="Query timeout in seconds")

@mcp.tool()
async def execute_query(
    ctx: Context,
    query_params: QueryParams
) -> dict:
    """
    Execute a SQL query against the database.

    Returns:
        dict: Query results with rows and metadata
    """
    db_pool = ctx.request_context.lifespan_context.db_pool

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(
            query_params.sql,
            *(query_params.params or []),
            timeout=query_params.timeout
        )

    return {
        "rows": [dict(row) for row in rows],
        "count": len(rows)
    }
```

**Why**:
- FastMCP automatically converts Pydantic models to JSON schema for LLM consumption
- Built-in validation with helpful error messages
- Type safety and IDE autocomplete
- Self-documenting with Field descriptions

**Alternatives**:
- **Individual parameters**: Better for simple tools with 1-3 parameters
- **TypedDict**: Less validation, but simpler for read-only structures

**⚠️ Known Issue**: Nested Pydantic models can have serialization issues where the LLM sends stringified JSON instead of objects. See workaround in [Common Pitfalls](#61-pydantic-serialization-issues).

---

### 1.2 Error Handling Best Practices

**Decision**: Use `ToolError` for all user-facing errors with specific, actionable messages.

**Pattern**:

```python
from fastmcp import FastMCP, ToolError
from pydantic import ValidationError
import asyncpg

@mcp.tool()
async def get_table_schema(ctx: Context, table_name: str) -> dict:
    """Get schema information for a database table."""

    # Input validation
    if not table_name or not table_name.strip():
        raise ToolError("Table name cannot be empty")

    if ";" in table_name or "--" in table_name:
        raise ToolError(
            "Invalid table name: contains SQL injection patterns. "
            "Use only alphanumeric characters and underscores."
        )

    db_pool = ctx.request_context.lifespan_context.db_pool

    try:
        async with db_pool.acquire() as conn:
            schema = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = $1
                ORDER BY ordinal_position
            """, table_name)

            if not schema:
                raise ToolError(
                    f"Table '{table_name}' not found. "
                    f"Use list_tables tool to see available tables."
                )

            return {
                "table": table_name,
                "columns": [dict(col) for col in schema]
            }

    except asyncpg.PostgresError as e:
        # Database-specific errors
        raise ToolError(f"Database error: {e.message}")

    except asyncpg.TimeoutError:
        raise ToolError(
            "Query timeout. The database may be overloaded. "
            "Try again in a few moments."
        )

    except Exception as e:
        # Unexpected errors - mask in production
        if mcp.config.get("mask_error_details", True):
            raise ToolError("Internal server error. Please contact support.")
        else:
            raise ToolError(f"Unexpected error: {type(e).__name__}: {str(e)}")
```

**Error Categories**:

| Error Type | When to Use | Example |
|------------|-------------|---------|
| `ToolError` | All user-facing errors | Invalid input, resource not found |
| `ValidationError` (Pydantic) | Auto-handled by FastMCP | Type mismatches, constraint violations |
| Protocol Errors | Auto-handled by MCP SDK | Malformed JSON-RPC messages |

**Best Practices**:
1. **Be specific**: "Table 'users' not found" > "Error"
2. **Be actionable**: Tell the LLM what to do next
3. **Mask sensitive details**: Use `mask_error_details=True` in production
4. **Catch specific exceptions**: Handle `FileNotFoundError` differently than `PermissionError`
5. **Layer error handling**: Validate inputs → Catch specific exceptions → Handle unexpected

**Rationale**:
- `ToolError` messages are passed directly to the LLM, enabling self-correction
- Generic exceptions are masked, preventing information leakage
- Actionable messages reduce retry cycles

---

### 1.3 Async Tool Implementation

**Decision**: Use `async def` for all I/O-bound operations (database, network, file I/O).

**Pattern**:

```python
@mcp.tool()
async def batch_query(ctx: Context, queries: list[str]) -> list[dict]:
    """
    Execute multiple queries concurrently.

    Args:
        queries: List of SQL queries to execute

    Returns:
        List of query results in the same order
    """
    db_pool = ctx.request_context.lifespan_context.db_pool

    async def execute_one(sql: str) -> dict:
        async with db_pool.acquire() as conn:
            try:
                rows = await conn.fetch(sql)
                return {
                    "success": True,
                    "rows": [dict(row) for row in rows],
                    "count": len(rows)
                }
            except asyncpg.PostgresError as e:
                return {
                    "success": False,
                    "error": str(e)
                }

    # Execute concurrently
    import asyncio
    results = await asyncio.gather(*[execute_one(q) for q in queries])
    return results
```

**Why Async**:
- FastMCP runs sync functions in a threadpool (overhead)
- Async functions run on the event loop (efficient)
- Database connections are async-native (asyncpg)
- Enables concurrent request handling

**When to Use Sync**:
- CPU-bound operations (data processing, computation)
- Third-party blocking libraries without async support

---

## 2. Resources Exposure

### 2.1 Dynamic Resource Generation

**Decision**: Use resource templates with URI patterns for database schemas and dynamic content.

**Pattern**:

```python
from fastmcp import FastMCP

mcp = FastMCP("postgres-mcp")

@mcp.resource("schema://{database}/{table}")
async def table_schema_resource(
    ctx: Context,
    database: str,
    table: str
) -> str:
    """
    Expose table schema as a resource.

    URI: schema://mydb/users
    """
    db_pool = ctx.request_context.lifespan_context.db_pool

    async with db_pool.acquire() as conn:
        # Get table schema
        columns = await conn.fetch("""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default,
                character_maximum_length
            FROM information_schema.columns
            WHERE table_catalog = $1 AND table_name = $2
            ORDER BY ordinal_position
        """, database, table)

        # Get constraints
        constraints = await conn.fetch("""
            SELECT constraint_name, constraint_type
            FROM information_schema.table_constraints
            WHERE table_catalog = $1 AND table_name = $2
        """, database, table)

        # Format as YAML for readability
        import yaml
        schema_data = {
            "database": database,
            "table": table,
            "columns": [dict(col) for col in columns],
            "constraints": [dict(c) for c in constraints]
        }

        return yaml.dump(schema_data, default_flow_style=False)


@mcp.resource("query-history://recent")
async def recent_queries_resource(ctx: Context) -> str:
    """
    Expose recent query history as a resource.

    URI: query-history://recent
    """
    # Fetch from cache or database
    history = ctx.request_context.lifespan_context.query_cache.get_recent(10)

    import json
    return json.dumps({
        "queries": history,
        "count": len(history)
    }, indent=2)
```

**URI Pattern Best Practices**:
- Use custom schemes for namespacing: `schema://`, `query://`, `stats://`
- Hierarchical structure: `{scheme}://{database}/{table}/{column}`
- Descriptive parameter names in templates
- Document available resources in server metadata

**Resource Content Formats**:
- **JSON**: Structured data, easy to parse
- **YAML**: Human-readable, good for schemas
- **Markdown**: Documentation, formatted output
- **CSV/TSV**: Tabular data exports

**Rationale**:
- Resources provide read-only access to server state
- Dynamic templates avoid pre-registering every table/schema
- LLMs can discover and reference resources by URI
- Separation of concerns: Tools for actions, Resources for data

---

### 2.2 Resource Update Mechanism

**Decision**: Use lifespan context to cache resources with time-based invalidation.

**Pattern**:

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional
import asyncio

@dataclass
class CachedResource:
    content: str
    timestamp: datetime
    ttl_seconds: int = 300  # 5 minutes

    def is_expired(self) -> bool:
        return datetime.now() - self.timestamp > timedelta(seconds=self.ttl_seconds)

class ResourceCache:
    """Thread-safe cache for dynamic resources."""

    def __init__(self):
        self._cache: dict[str, CachedResource] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[str]:
        async with self._lock:
            cached = self._cache.get(key)
            if cached and not cached.is_expired():
                return cached.content
            return None

    async def set(self, key: str, content: str, ttl: int = 300):
        async with self._lock:
            self._cache[key] = CachedResource(
                content=content,
                timestamp=datetime.now(),
                ttl_seconds=ttl
            )

    async def invalidate(self, pattern: str):
        """Invalidate all keys matching pattern."""
        async with self._lock:
            keys_to_delete = [k for k in self._cache if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]


@mcp.resource("schema://{database}/{table}")
async def cached_table_schema(ctx: Context, database: str, table: str) -> str:
    """Cached table schema resource."""
    cache: ResourceCache = ctx.request_context.lifespan_context.resource_cache
    cache_key = f"schema:{database}:{table}"

    # Check cache
    cached = await cache.get(cache_key)
    if cached:
        return cached

    # Fetch from database
    db_pool = ctx.request_context.lifespan_context.db_pool
    async with db_pool.acquire() as conn:
        schema_data = await fetch_schema(conn, database, table)

    # Cache result
    content = format_schema(schema_data)
    await cache.set(cache_key, content, ttl=600)  # 10 min TTL

    return content


@mcp.tool()
async def invalidate_schema_cache(ctx: Context, table_name: str):
    """Invalidate cached schema for a table after DDL changes."""
    cache = ctx.request_context.lifespan_context.resource_cache
    await cache.invalidate(f"schema:*:{table_name}")
```

**Invalidation Strategies**:
1. **Time-based (TTL)**: Automatic expiration after N seconds
2. **Event-based**: Invalidate after schema changes (DDL)
3. **Manual**: Tool to explicitly clear cache
4. **Size-based**: LRU eviction when cache grows too large

---

## 3. Context Management

### 3.1 Lifespan and State Management

**Decision**: Use async context manager with typed dataclass for server state.

**Complete Pattern**:

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Optional
import asyncpg
import logging

@dataclass
class AppContext:
    """Server-wide application context."""
    db_pool: asyncpg.Pool
    resource_cache: ResourceCache
    query_history: QueryHistory
    config: dict
    logger: logging.Logger


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """
    Manage application lifecycle.

    Initializes on server startup, yields context for all requests,
    cleans up on server shutdown.
    """
    # Setup logging
    logger = logging.getLogger("postgres-mcp")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    logger.addHandler(handler)

    logger.info("Starting PostgreSQL MCP Server...")

    # Load configuration
    config = load_config()  # From env vars or config file

    # Initialize database pool
    logger.info(f"Connecting to database: {config['db_host']}")
    db_pool = await asyncpg.create_pool(
        host=config["db_host"],
        port=config.get("db_port", 5432),
        user=config["db_user"],
        password=config["db_password"],
        database=config["db_name"],
        min_size=config.get("pool_min_size", 2),
        max_size=config.get("pool_max_size", 10),
        command_timeout=config.get("command_timeout", 60),
        # Connection pool settings
        max_inactive_connection_lifetime=300,  # 5 min
    )

    # Test connection
    async with db_pool.acquire() as conn:
        version = await conn.fetchval("SELECT version()")
        logger.info(f"Connected to: {version}")

    # Initialize caches and state
    resource_cache = ResourceCache()
    query_history = QueryHistory(max_size=1000)

    try:
        # Yield context for request handlers
        context = AppContext(
            db_pool=db_pool,
            resource_cache=resource_cache,
            query_history=query_history,
            config=config,
            logger=logger
        )
        logger.info("Server ready")
        yield context

    finally:
        # Cleanup on shutdown
        logger.info("Shutting down...")

        # Close database pool gracefully
        await db_pool.close()
        logger.info("Database pool closed")

        # Clear caches
        await resource_cache.clear()

        logger.info("Shutdown complete")


# Create MCP server with lifespan
mcp = FastMCP(
    "postgres-mcp",
    version="1.0.0",
    lifespan=app_lifespan
)
```

**Accessing Context in Tools**:

```python
@mcp.tool()
async def execute_query(ctx: Context, sql: str) -> dict:
    """Execute a SQL query."""
    # Access lifespan context
    app_ctx: AppContext = ctx.request_context.lifespan_context

    # Use shared resources
    logger = app_ctx.logger
    db_pool = app_ctx.db_pool
    history = app_ctx.query_history

    logger.info(f"Executing query: {sql[:100]}...")

    async with db_pool.acquire() as conn:
        rows = await conn.fetch(sql)

    # Record in history
    await history.add(sql, len(rows))

    return {"rows": [dict(row) for row in rows]}
```

**Why This Pattern**:
- **Single initialization**: Pool created once, reused for all requests
- **Graceful shutdown**: Ensures connections are closed properly
- **Type safety**: IDE autocomplete for context attributes
- **Centralized config**: All settings in one place
- **Logging**: Consistent logger available to all tools

---

### 3.2 Request Context Propagation

**Decision**: Use Context parameter for request-specific data (user_id, request_id, auth).

**Pattern**:

```python
from uuid import uuid4

class RequestContext:
    """Per-request context data."""

    def __init__(self):
        self.request_id: str = str(uuid4())
        self.user_id: Optional[str] = None
        self.start_time: datetime = datetime.now()
        self.metadata: dict = {}


@mcp.tool()
async def execute_query(ctx: Context, sql: str) -> dict:
    """Execute a query with request tracking."""
    app_ctx = ctx.request_context.lifespan_context

    # Generate request ID if not present
    request_id = getattr(ctx, "request_id", str(uuid4()))

    app_ctx.logger.info(
        f"[{request_id}] Query execution started",
        extra={"request_id": request_id, "sql": sql}
    )

    try:
        async with app_ctx.db_pool.acquire() as conn:
            # Set application_name for connection tracking
            await conn.execute(f"SET application_name TO 'mcp-{request_id[:8]}'")
            rows = await conn.fetch(sql)

        app_ctx.logger.info(
            f"[{request_id}] Query completed: {len(rows)} rows",
            extra={"request_id": request_id, "row_count": len(rows)}
        )

        return {"rows": [dict(row) for row in rows]}

    except Exception as e:
        app_ctx.logger.error(
            f"[{request_id}] Query failed: {e}",
            extra={"request_id": request_id, "error": str(e)}
        )
        raise
```

**⚠️ Thread Safety Issue**: In FastMCP with StreamableHTTP transport, request context can be stale across multiple requests in the same session. See [Common Pitfalls](#64-stale-context-in-concurrent-requests) for workaround.

---

## 4. Integration with Asyncpg

### 4.1 Connection Pool Initialization

**Decision**: Initialize pool in lifespan with production-ready settings.

**Production Configuration**:

```python
import asyncpg
from typing import Optional

async def create_production_pool(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    min_size: int = 2,
    max_size: int = 10,
    max_queries: int = 50000,
    max_inactive_connection_lifetime: float = 300.0,
    timeout: float = 60.0,
    command_timeout: Optional[float] = None,
    server_settings: Optional[dict] = None,
) -> asyncpg.Pool:
    """
    Create a production-ready asyncpg connection pool.

    Args:
        min_size: Minimum number of connections (keep warm)
        max_size: Maximum number of connections
        max_queries: Max queries per connection before recycling
        max_inactive_connection_lifetime: Close idle connections after N seconds
        timeout: Connection acquisition timeout
        command_timeout: Default query timeout (None = no timeout)
        server_settings: PostgreSQL session variables
    """
    pool = await asyncpg.create_pool(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        min_size=min_size,
        max_size=max_size,
        max_queries=max_queries,
        max_inactive_connection_lifetime=max_inactive_connection_lifetime,
        timeout=timeout,
        command_timeout=command_timeout,
        server_settings=server_settings or {
            "application_name": "fastmcp-postgres",
            "timezone": "UTC",
        },
    )

    return pool


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Lifespan with production pool settings."""

    # Read from environment
    import os
    db_config = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": int(os.getenv("POSTGRES_PORT", "5432")),
        "user": os.getenv("POSTGRES_USER", "postgres"),
        "password": os.getenv("POSTGRES_PASSWORD", ""),
        "database": os.getenv("POSTGRES_DB", "postgres"),
        "min_size": int(os.getenv("POOL_MIN_SIZE", "2")),
        "max_size": int(os.getenv("POOL_MAX_SIZE", "10")),
    }

    pool = await create_production_pool(**db_config)

    try:
        yield AppContext(db_pool=pool, ...)
    finally:
        await pool.close()
```

**Pool Sizing Guidelines**:
- **min_size**: 2-5 (keep connections warm, avoid cold starts)
- **max_size**: 10-20 for typical workloads (PostgreSQL has connection limits)
- **max_queries**: 50000 (recycle connections to prevent memory leaks)
- **max_inactive_connection_lifetime**: 300s (5 min, close idle connections)
- **timeout**: 60s (connection acquisition timeout)
- **command_timeout**: 30-60s (prevent runaway queries)

---

### 4.2 Connection Acquisition Patterns

**Decision**: Use `async with pool.acquire()` for automatic connection management.

**Basic Pattern**:

```python
@mcp.tool()
async def get_user(ctx: Context, user_id: int) -> dict:
    """Fetch a single user."""
    db_pool = ctx.request_context.lifespan_context.db_pool

    async with db_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, name, email FROM users WHERE id = $1",
            user_id
        )

        if row is None:
            raise ToolError(f"User {user_id} not found")

        return dict(row)
```

**Transaction Pattern**:

```python
@mcp.tool()
async def transfer_funds(
    ctx: Context,
    from_account: int,
    to_account: int,
    amount: float
) -> dict:
    """Transfer funds between accounts atomically."""
    db_pool = ctx.request_context.lifespan_context.db_pool

    async with db_pool.acquire() as conn:
        async with conn.transaction():
            # Debit from source
            await conn.execute(
                "UPDATE accounts SET balance = balance - $1 WHERE id = $2",
                amount, from_account
            )

            # Credit to destination
            await conn.execute(
                "UPDATE accounts SET balance = balance + $1 WHERE id = $2",
                amount, to_account
            )

            # Log transaction
            tx_id = await conn.fetchval(
                """
                INSERT INTO transactions (from_account, to_account, amount)
                VALUES ($1, $2, $3)
                RETURNING id
                """,
                from_account, to_account, amount
            )

            return {"transaction_id": tx_id, "status": "completed"}
```

**Batch Operations**:

```python
@mcp.tool()
async def bulk_insert(ctx: Context, records: list[dict]) -> dict:
    """Insert multiple records efficiently."""
    db_pool = ctx.request_context.lifespan_context.db_pool

    async with db_pool.acquire() as conn:
        # Use COPY for bulk inserts (fastest method)
        await conn.copy_records_to_table(
            "users",
            records=records,
            columns=["name", "email", "created_at"]
        )

        return {"inserted": len(records)}
```

**Connection Pooling Benefits**:
- Automatic connection lifecycle management
- Connection reuse (no overhead per request)
- Graceful handling of connection failures
- Prevents connection leaks

---

### 4.3 Error Propagation and Recovery

**Decision**: Catch asyncpg exceptions and convert to ToolError with context.

**Comprehensive Error Handling**:

```python
import asyncpg

@mcp.tool()
async def execute_query(ctx: Context, sql: str, params: list = None) -> dict:
    """Execute a SQL query with comprehensive error handling."""
    db_pool = ctx.request_context.lifespan_context.db_pool
    params = params or []

    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return {
                "rows": [dict(row) for row in rows],
                "count": len(rows)
            }

    # Connection/network errors
    except asyncpg.PostgresConnectionError as e:
        raise ToolError(
            "Database connection lost. The server may be restarting. "
            "Please try again in a moment."
        )

    # Query timeout
    except asyncpg.QueryCanceledError:
        raise ToolError(
            f"Query exceeded timeout limit. "
            f"Try simplifying the query or adding appropriate indexes."
        )

    # Syntax errors
    except asyncpg.PostgresSyntaxError as e:
        raise ToolError(
            f"SQL syntax error: {e.message}\n"
            f"Position: {getattr(e, 'position', 'unknown')}"
        )

    # Constraint violations
    except asyncpg.UniqueViolationError as e:
        raise ToolError(
            f"Unique constraint violation: {e.detail or e.message}\n"
            f"A record with this value already exists."
        )

    except asyncpg.ForeignKeyViolationError as e:
        raise ToolError(
            f"Foreign key constraint violation: {e.detail or e.message}\n"
            f"Referenced record does not exist."
        )

    except asyncpg.NotNullViolationError as e:
        raise ToolError(
            f"Required field missing: {e.column_name or e.message}\n"
            f"This field cannot be null."
        )

    # Permission errors
    except asyncpg.InsufficientPrivilegeError as e:
        raise ToolError(
            f"Permission denied: {e.message}\n"
            f"The database user lacks necessary privileges."
        )

    # Generic PostgreSQL errors
    except asyncpg.PostgresError as e:
        raise ToolError(
            f"Database error ({e.sqlstate}): {e.message}"
        )

    # Pool exhaustion
    except asyncio.TimeoutError:
        raise ToolError(
            "Connection pool timeout. The server is overloaded. "
            "Please try again shortly."
        )

    # Unexpected errors
    except Exception as e:
        ctx.request_context.lifespan_context.logger.exception(
            f"Unexpected error in execute_query: {e}"
        )
        raise ToolError(
            "An unexpected error occurred. Please contact support."
        )
```

**Recovery Strategies**:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True
)
async def execute_with_retry(pool: asyncpg.Pool, sql: str, *params):
    """Execute query with automatic retry on transient failures."""
    async with pool.acquire() as conn:
        return await conn.fetch(sql, *params)


@mcp.tool()
async def resilient_query(ctx: Context, sql: str) -> dict:
    """Execute query with retry logic."""
    db_pool = ctx.request_context.lifespan_context.db_pool

    try:
        rows = await execute_with_retry(db_pool, sql)
        return {"rows": [dict(row) for row in rows]}
    except asyncpg.PostgresConnectionError as e:
        raise ToolError(
            "Database is temporarily unavailable after 3 retry attempts. "
            "Please try again later."
        )
```

---

### 4.4 Concurrent Request Handling

**Decision**: FastMCP automatically handles concurrent requests via asyncio event loop.

**Concurrency Pattern**:

```python
@mcp.tool()
async def parallel_queries(ctx: Context, tables: list[str]) -> dict:
    """Execute queries on multiple tables concurrently."""
    db_pool = ctx.request_context.lifespan_context.db_pool

    async def count_table(table: str) -> tuple[str, int]:
        """Count rows in a single table."""
        async with db_pool.acquire() as conn:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            return table, count

    # Execute concurrently (limited by pool size)
    import asyncio
    results = await asyncio.gather(
        *[count_table(table) for table in tables],
        return_exceptions=True  # Don't fail entire batch on single error
    )

    # Process results
    counts = {}
    errors = {}
    for table, result in zip(tables, results):
        if isinstance(result, Exception):
            errors[table] = str(result)
        else:
            table_name, count = result
            counts[table_name] = count

    return {
        "counts": counts,
        "errors": errors if errors else None
    }
```

**Thread Safety Notes**:
- **Pool is thread-safe**: Can be shared across multiple async tasks
- **Connections are NOT thread-safe**: Each task must acquire its own connection
- **Context managers handle cleanup**: Even if task is cancelled
- **Pool limits concurrency**: Max concurrent connections = `max_size`

---

## 5. Architecture Patterns

### 5.1 Recommended Project Structure

```
postgres-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py              # FastMCP server initialization
│   ├── config.py              # Configuration management
│   ├── tools/                 # MCP tools (grouped by domain)
│   │   ├── __init__.py
│   │   ├── query.py           # Query execution tools
│   │   ├── schema.py          # Schema inspection tools
│   │   ├── management.py      # Admin tools
│   │   └── utils.py           # Shared utilities
│   ├── resources/             # MCP resources
│   │   ├── __init__.py
│   │   ├── schema.py          # Schema resources
│   │   └── stats.py           # Statistics resources
│   ├── models.py              # Pydantic models
│   ├── context.py             # Context management
│   ├── cache.py               # Caching layer
│   └── errors.py              # Custom exceptions
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py            # Pytest fixtures
├── pyproject.toml
├── .env.example
└── README.md
```

### 5.2 Layered Architecture

```python
# src/server.py - Server initialization
from fastmcp import FastMCP
from .context import app_lifespan
from .tools import register_tools
from .resources import register_resources

def create_server() -> FastMCP:
    """Create and configure the FastMCP server."""
    mcp = FastMCP(
        "postgres-mcp",
        version="1.0.0",
        lifespan=app_lifespan
    )

    # Register tools and resources
    register_tools(mcp)
    register_resources(mcp)

    return mcp

# Entry point
mcp = create_server()


# src/tools/__init__.py - Tool registration
from .query import execute_query, batch_query
from .schema import get_table_schema, list_tables
from .management import vacuum_table, analyze_table

def register_tools(mcp: FastMCP):
    """Register all tools with the server."""
    # Query tools
    mcp.tool()(execute_query)
    mcp.tool()(batch_query)

    # Schema tools
    mcp.tool()(get_table_schema)
    mcp.tool()(list_tables)

    # Management tools
    mcp.tool()(vacuum_table)
    mcp.tool()(analyze_table)


# src/tools/query.py - Domain-specific tools
from fastmcp import Context, ToolError
from ..models import QueryParams
import asyncpg

async def execute_query(ctx: Context, params: QueryParams) -> dict:
    """Execute a SQL query."""
    db_pool = ctx.request_context.lifespan_context.db_pool

    try:
        async with db_pool.acquire() as conn:
            rows = await conn.fetch(params.sql, *params.params)
            return {
                "rows": [dict(row) for row in rows],
                "count": len(rows)
            }
    except asyncpg.PostgresError as e:
        raise ToolError(f"Query failed: {e.message}")


# src/models.py - Shared data models
from pydantic import BaseModel, Field
from typing import Optional

class QueryParams(BaseModel):
    sql: str = Field(..., description="SQL query to execute")
    params: list = Field(default_factory=list, description="Query parameters")
    timeout: float = Field(default=30.0, description="Query timeout in seconds")


# src/config.py - Configuration management
from pydantic_settings import BaseSettings
from typing import Optional

class Config(BaseSettings):
    """Server configuration from environment variables."""

    # Database
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "postgres"
    postgres_password: str
    postgres_db: str = "postgres"

    # Pool settings
    pool_min_size: int = 2
    pool_max_size: int = 10
    pool_timeout: float = 60.0

    # Server settings
    log_level: str = "INFO"
    mask_error_details: bool = True

    class Config:
        env_file = ".env"

def load_config() -> Config:
    return Config()
```

**Benefits**:
- **Separation of concerns**: Tools, resources, models, config are isolated
- **Testability**: Each module can be tested independently
- **Maintainability**: Easy to add new tools without touching existing code
- **Discoverability**: Clear structure for new developers

---

### 5.3 Testing Strategy

```python
# tests/conftest.py - Shared fixtures
import pytest
import asyncpg
from fastmcp import FastMCP
from src.server import create_server

@pytest.fixture
async def db_pool():
    """Create a test database pool."""
    pool = await asyncpg.create_pool(
        host="localhost",
        port=5432,
        user="test",
        password="test",
        database="test_db",
        min_size=1,
        max_size=2
    )

    # Setup test schema
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_users (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL
            )
        """)

    yield pool

    # Cleanup
    await pool.close()


@pytest.fixture
def mcp_server():
    """Create a test MCP server."""
    return create_server()


# tests/unit/test_tools.py - Unit tests
import pytest
from fastmcp import Context, ToolError
from src.tools.query import execute_query
from src.models import QueryParams

@pytest.mark.asyncio
async def test_execute_query_success(db_pool, mocker):
    """Test successful query execution."""
    # Mock context
    ctx = mocker.Mock(spec=Context)
    ctx.request_context.lifespan_context.db_pool = db_pool

    # Execute query
    params = QueryParams(sql="SELECT 1 as num")
    result = await execute_query(ctx, params)

    assert result["count"] == 1
    assert result["rows"][0]["num"] == 1


@pytest.mark.asyncio
async def test_execute_query_syntax_error(db_pool, mocker):
    """Test query with syntax error."""
    ctx = mocker.Mock(spec=Context)
    ctx.request_context.lifespan_context.db_pool = db_pool

    params = QueryParams(sql="SELECT * FORM users")  # FORM typo

    with pytest.raises(ToolError, match="syntax error"):
        await execute_query(ctx, params)


# tests/integration/test_server.py - Integration tests
@pytest.mark.asyncio
async def test_full_server_lifecycle(mcp_server, db_pool):
    """Test server startup, tool execution, shutdown."""
    # Simulate server lifecycle
    async with mcp_server.lifespan_context() as ctx:
        assert ctx.db_pool is not None

        # Execute a tool
        result = await mcp_server.call_tool(
            "execute_query",
            {"sql": "SELECT version()"}
        )

        assert result["count"] == 1
```

---

## 6. Common Pitfalls and Troubleshooting

### 6.1 Pydantic Serialization Issues

**Problem**: LLM sends Pydantic model parameters as stringified JSON instead of objects.

**Symptom**:
```
ValidationError: '{"name": "Alice"}' is not of type 'object'
```

**Root Cause**: FastMCP's schema generation can confuse some LLMs, causing them to serialize nested models as strings.

**Workaround 1: Flatten Parameters**

```python
# ❌ BAD: Nested Pydantic model
class UserCreate(BaseModel):
    name: str
    email: str
    age: int

@mcp.tool()
async def create_user(ctx: Context, user: UserCreate) -> dict:
    ...

# ✅ GOOD: Individual parameters
@mcp.tool()
async def create_user(
    ctx: Context,
    name: str,
    email: str,
    age: int
) -> dict:
    """Create a new user."""
    # Create model internally
    user = UserCreate(name=name, email=email, age=age)
    # ... rest of logic
```

**Workaround 2: Accept JSON String**

```python
import json

@mcp.tool()
async def create_user(ctx: Context, user_json: str) -> dict:
    """Create a user from JSON string."""
    try:
        user_data = json.loads(user_json)
        user = UserCreate(**user_data)
    except json.JSONDecodeError:
        raise ToolError("Invalid JSON format")
    except ValidationError as e:
        raise ToolError(f"Validation failed: {e}")

    # ... rest of logic
```

**Status**: This is a known issue in FastMCP < 3.0. Check if resolved in 3.0.0b1+.

---

### 6.2 Connection Pool Exhaustion

**Problem**: Server hangs or times out under load.

**Symptom**:
```
TimeoutError: Connection pool timeout
```

**Root Cause**: All connections are in use, and new requests are waiting.

**Solutions**:

1. **Increase pool size**:
```python
pool = await asyncpg.create_pool(max_size=20)  # Was 10
```

2. **Add connection timeout**:
```python
pool = await asyncpg.create_pool(
    max_size=10,
    timeout=30.0  # Fail fast instead of hanging
)
```

3. **Monitor pool usage**:
```python
@mcp.tool()
async def pool_stats(ctx: Context) -> dict:
    """Get connection pool statistics."""
    pool = ctx.request_context.lifespan_context.db_pool
    return {
        "size": pool.get_size(),
        "free": pool.get_idle_size(),
        "in_use": pool.get_size() - pool.get_idle_size(),
        "max_size": pool._max_size
    }
```

4. **Use query timeouts**:
```python
async with pool.acquire() as conn:
    await conn.fetch(sql, timeout=10.0)  # Kill long queries
```

---

### 6.3 Memory Leaks from Unclosed Connections

**Problem**: Memory usage grows over time, eventually causing OOM.

**Root Cause**: Connections not returned to pool (missing `async with`).

**❌ BAD: Manual connection management**
```python
conn = await pool.acquire()
rows = await conn.fetch(sql)
# Connection leaked if exception occurs here!
await pool.release(conn)
```

**✅ GOOD: Context manager**
```python
async with pool.acquire() as conn:
    rows = await conn.fetch(sql)
# Connection always returned, even on exception
```

**Detection**:
```python
# Add logging in lifespan shutdown
async def app_lifespan(server: FastMCP):
    pool = await asyncpg.create_pool(...)
    try:
        yield AppContext(db_pool=pool)
    finally:
        logger.warning(f"Active connections at shutdown: {pool.get_size()}")
        await pool.close()
```

---

### 6.4 Stale Context in Concurrent Requests

**Problem**: In StreamableHTTP transport, request context from the first HTTP request is used for all subsequent requests in the same session.

**Symptom**: User ID, request ID, or other per-request data is incorrect.

**Root Cause**: FastMCP bug with context propagation in StreamableHTTP.

**Workaround: Thread-safe Request Store**

```python
from threading import RLock
from typing import Optional
from uuid import uuid4

class ThreadSafeRequestStore:
    """Thread-safe storage for per-request context."""

    def __init__(self):
        self.store: dict[str, dict] = {}
        self.lock = RLock()

    def set(self, request_id: str, data: dict):
        with self.lock:
            self.store[request_id] = data

    def get(self, request_id: str) -> Optional[dict]:
        with self.lock:
            return self.store.get(request_id)

    def remove(self, request_id: str):
        with self.lock:
            self.store.pop(request_id, None)


# Global request store
request_store = ThreadSafeRequestStore()


@mcp.tool()
async def track_request(ctx: Context, user_id: str) -> dict:
    """Tool with per-request tracking."""
    request_id = str(uuid4())

    # Store request context
    request_store.set(request_id, {
        "user_id": user_id,
        "timestamp": datetime.now()
    })

    try:
        # Use request_id throughout tool execution
        logger.info(f"[{request_id}] Processing for user {user_id}")

        # ... tool logic ...

        return {"request_id": request_id, "status": "success"}

    finally:
        # Cleanup
        request_store.remove(request_id)
```

**Status**: Check if resolved in FastMCP 3.0+.

---

### 6.5 Tool Registration Issues

**Problem**: Tools not showing up in LLM.

**Checklist**:

1. **Decorator applied?**
```python
@mcp.tool()  # ← Don't forget!
async def my_tool(ctx: Context) -> dict:
    ...
```

2. **Type hints present?**
```python
# ❌ BAD: No type hints
@mcp.tool()
async def my_tool(ctx, param):  # Can't generate schema
    ...

# ✅ GOOD: Full type hints
@mcp.tool()
async def my_tool(ctx: Context, param: str) -> dict:
    ...
```

3. **Server running?**
```bash
# Check if server is accessible
curl http://localhost:8000/health  # Or equivalent
```

4. **Logs available?**
```bash
# Check MCP logs (macOS)
tail -f ~/Library/Logs/Claude/mcp-server-*.log
```

---

### 6.6 Error Message Best Practices

**❌ BAD: Vague errors**
```python
raise ToolError("Error")
raise ToolError(str(e))  # Leaks internal details
```

**✅ GOOD: Specific, actionable errors**
```python
# User input errors
raise ToolError(
    "Table name 'users-table' is invalid. "
    "Use only letters, numbers, and underscores."
)

# Resource not found
raise ToolError(
    f"Table '{table_name}' not found. "
    f"Use list_tables() to see available tables."
)

# Permission errors
raise ToolError(
    "Insufficient permissions to drop table. "
    "This operation requires superuser privileges."
)

# Transient errors
raise ToolError(
    "Database connection lost. "
    "The server may be restarting. Try again in a moment."
)
```

---

### 6.7 Performance Optimization

**Common Issues and Solutions**:

| Issue | Solution |
|-------|----------|
| Slow queries | Add indexes, use EXPLAIN ANALYZE |
| N+1 queries | Use JOINs or batch fetching |
| Large result sets | Pagination, LIMIT/OFFSET |
| Connection overhead | Increase `min_size` for connection pooling |
| Serialization overhead | Use `asyncpg.Record` directly, avoid `dict()` conversion |

**Example: Efficient Pagination**

```python
@mcp.tool()
async def list_users_paginated(
    ctx: Context,
    page: int = 1,
    page_size: int = 100
) -> dict:
    """List users with efficient pagination."""
    if page < 1:
        raise ToolError("Page must be >= 1")
    if page_size > 1000:
        raise ToolError("Page size cannot exceed 1000")

    offset = (page - 1) * page_size

    db_pool = ctx.request_context.lifespan_context.db_pool
    async with db_pool.acquire() as conn:
        # Fetch one extra row to check if there's a next page
        rows = await conn.fetch(
            "SELECT id, name, email FROM users ORDER BY id LIMIT $1 OFFSET $2",
            page_size + 1,
            offset
        )

    has_next = len(rows) > page_size
    users = [dict(row) for row in rows[:page_size]]

    return {
        "users": users,
        "page": page,
        "page_size": page_size,
        "has_next": has_next
    }
```

---

## Summary: Decision Matrix

| Aspect | Recommended Approach | Alternative | When to Use Alternative |
|--------|---------------------|-------------|------------------------|
| **Tool Inputs** | Pydantic models | Individual params | Simple tools (1-3 params) |
| **Error Handling** | ToolError with specific messages | Generic exceptions | Never (always use ToolError) |
| **Async/Sync** | async def | def (threadpool) | CPU-bound, blocking libraries |
| **Resources** | Dynamic templates | Static resources | Small, fixed resource set |
| **Lifespan** | Async context manager | Global state | Never (use lifespan) |
| **Pool Size** | 10-20 connections | 50+ connections | Very high concurrency |
| **Connection Mgmt** | `async with pool.acquire()` | Manual acquire/release | Never (use context manager) |
| **Error Recovery** | Retry with exponential backoff | Fail fast | Critical operations only |
| **Caching** | Time-based (TTL) | Event-based invalidation | Frequently changing data |
| **Logging** | Structured logging (JSON) | Plain text | Development only |

---

## Additional Resources

### Official Documentation
- [FastMCP Documentation](https://gofastmcp.com)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [Asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [Model Context Protocol](https://spec.modelcontextprotocol.io/)

### Example Repositories
- Search GitHub for "fastmcp postgres" for community examples
- Check FastMCP examples directory for official samples

### Community
- FastMCP Discord/Discussions (check GitHub repo)
- MCP Community Forum

---

## Version Notes

- **FastMCP 3.0.0b1**: Beta release with new features (check changelog before using)
- **FastMCP 2.x**: Stable, production-ready
- **Asyncpg 0.28+**: Stable, recommended version
- **Python 3.11+**: Required for FastMCP

**Recommendation**: Pin to FastMCP 2.x for production (`fastmcp<3`) until 3.0 is stable.

---

## Next Steps

1. **Setup Project**: Use the recommended project structure
2. **Initialize Pool**: Implement lifespan with asyncpg pool
3. **Define Tools**: Start with essential query/schema tools
4. **Add Resources**: Expose schemas as dynamic resources
5. **Test**: Unit tests for tools, integration tests for server
6. **Monitor**: Add logging, pool stats, error tracking
7. **Optimize**: Profile and optimize hot paths

**Key Principles**:
- ✅ Always use `async with` for connections
- ✅ Raise `ToolError` with actionable messages
- ✅ Initialize pool in lifespan, never in tools
- ✅ Use type hints and Pydantic models
- ✅ Test with real asyncpg connection pool
- ✅ Monitor pool usage and connection lifecycle

---

**Document Status**: Complete
**Last Updated**: 2026-01-28
**Maintainer**: Research Team

## Sources

- [FastMCP Documentation](https://gofastmcp.com)
- [FastMCP Best Practices](https://gofastmcp.com/docs/best-practices)
- [FastMCP Error Handling Guide](https://gofastmcp.com/docs/error-handling)
- [FastMCP Lifecycle Management](https://gofastmcp.com/docs/lifecycle)
- [FastMCP Resources](https://gofastmcp.com/docs/resources)
- [Asyncpg Connection Pooling](https://magicstack.github.io/asyncpg/current/usage.html#connection-pools)
