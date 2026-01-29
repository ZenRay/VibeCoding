# Asyncpg Connection Pool Management Best Practices

**Date**: 2026-01-28
**Project**: Week5 - Multi-Database Query Tool
**Purpose**: Research and design connection pool architecture for 10+ concurrent queries across multiple PostgreSQL databases

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Connection Pool Configuration](#connection-pool-configuration)
3. [Health Checks and Reconnection](#health-checks-and-reconnection)
4. [Multi-Database Pool Management](#multi-database-pool-management)
5. [Transaction and Timeout Control](#transaction-and-timeout-control)
6. [Error Handling Strategies](#error-handling-strategies)
7. [Architecture Design](#architecture-design)
8. [Implementation](#implementation)
9. [References](#references)

---

## Executive Summary

### Key Findings

1. **Pool Sizing**: For 10+ concurrent queries, recommend `min_size=5, max_size=20` per database
2. **Multiple Databases**: Use **independent pools per database** (asyncpg doesn't support database switching)
3. **Timeout Configuration**: Set `statement_timeout=30s`, `idle_in_transaction_session_timeout=60s`
4. **Error Recovery**: Implement circuit breaker pattern for pool exhaustion, automatic schema cache invalidation
5. **Health Checks**: Leverage built-in `max_inactive_connection_lifetime=300s` instead of explicit checks

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   PoolManager (Singleton)                   │
├─────────────────────────────────────────────────────────────┤
│  - Manages multiple database pools                          │
│  - Handles dynamic pool creation/destruction                │
│  - Schema cache lifecycle management                        │
│  - Connection health monitoring                             │
└─────────────────────────────────────────────────────────────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
     ┌──────▼─────┐  ┌─────▼──────┐  ┌────▼───────┐
     │ Pool: DB1  │  │ Pool: DB2  │  │ Pool: DBN  │
     ├────────────┤  ├────────────┤  ├────────────┤
     │ min: 5     │  │ min: 5     │  │ min: 5     │
     │ max: 20    │  │ max: 20    │  │ max: 20    │
     │ timeout:300│  │ timeout:300│  │ timeout:300│
     └────────────┘  └────────────┘  └────────────┘
```

---

## Connection Pool Configuration

### 1.1 Pool Size Parameters

#### Recommended Configuration

```python
POOL_CONFIG = {
    "min_size": 5,              # Baseline connections (always ready)
    "max_size": 20,             # Peak concurrent load
    "max_queries": 50000,       # Recycle connection after 50k queries
    "max_inactive_connection_lifetime": 300.0,  # 5 minutes idle timeout
    "command_timeout": 60.0,    # 60 seconds per command
}
```

#### Calculation Formula

```python
# For N concurrent queries across M databases:
concurrent_queries = 10
databases = 5
safety_factor = 2  # Handle bursts

min_size_per_db = max(2, concurrent_queries // databases)
max_size_per_db = min_size_per_db * safety_factor

# Result: min_size=5, max_size=20 per database
```

#### Constraints

- `max_size` > 0
- `min_size` >= 0
- `min_size` <= `max_size`
- Consider PostgreSQL's `max_connections` limit (default 100)
- Multiple app instances must share the connection limit

### 1.2 Performance Benefits

- **Connection reuse**: Eliminates overhead of creating new connections
- **Latency reduction**: 10-100x faster for short queries
- **Resource efficiency**: Maintains baseline connections, scales to peak

### 1.3 Configuration Scope

Don't set timeouts globally in `postgresql.conf`. Use:
- Database-level: `ALTER DATABASE mydb SET statement_timeout = '30s';`
- User-level: `ALTER ROLE myuser SET statement_timeout = '30s';`
- Session-level: Via `server_settings` parameter in asyncpg

---

## Health Checks and Reconnection

### 2.1 Built-in Connection Lifecycle

asyncpg's pool automatically manages connection health through:

```python
max_inactive_connection_lifetime = 300.0  # Close idle connections after 5 min
max_queries = 50000  # Recycle connections after 50k queries
```

**Why this works:**
- Prevents connection degradation (memory leaks, stale state)
- Automatically cycles out unhealthy connections
- No explicit health check SQL needed

### 2.2 Connection Reset Behavior

When a connection is released back to the pool:
- ✅ Closes all open cursors
- ✅ Closes all open transactions
- ✅ Removes notification/log listeners
- ❌ **Keeps prepared statements cached** (for performance)

### 2.3 Schema Cache Invalidation

**Problem**: After `ALTER TABLE` or `SET search_path`, cached schema becomes stale

**Solution**: Automatic invalidation on error

```python
try:
    result = await conn.fetch("SELECT * FROM modified_table")
except asyncpg.OutdatedSchemaCacheError:
    await conn.reload_schema_state()
    result = await conn.fetch("SELECT * FROM modified_table")
```

**Pool-wide cache clearing**: When `InvalidCachedStatementError` occurs, asyncpg clears the cache for **all connections in the pool**.

### 2.4 Reconnection Strategy

**Automatic reconnection**: asyncpg doesn't auto-reconnect. Use exponential backoff:

```python
async def acquire_with_retry(
    pool: asyncpg.Pool,
    max_retries: int = 3,
    base_delay: float = 1.0
) -> asyncpg.Connection:
    for attempt in range(max_retries):
        try:
            return await pool.acquire(timeout=10.0)
        except asyncpg.PoolTimeoutError:
            if attempt == max_retries - 1:
                raise
            delay = base_delay * (2 ** attempt)  # Exponential backoff
            await asyncio.sleep(delay)
```

---

## Multi-Database Pool Management

### 3.1 Architecture Decision: Independent Pools

**Why not shared pool?**
- asyncpg doesn't support `USE database` or connection switching
- Each pool connects to a single database on a PostgreSQL server
- TLS connections to different databases are expensive to multiplex

**Design**: One `asyncpg.Pool` per database connection string

```python
{
    "db_id_1": Pool(host=..., database="db1", ...),
    "db_id_2": Pool(host=..., database="db2", ...),
    "db_id_N": Pool(host=..., database="dbN", ...),
}
```

### 3.2 Pool Lifecycle Management

#### Creation Timing
- **Preconfigured databases**: Create pools on application startup
- **Dynamic databases**: Create pool on first query request

#### Destruction Timing
- **Graceful shutdown**: Close all pools on app shutdown
- **Idle timeout**: Close pool if no queries for 30 minutes (configurable)
- **Manual removal**: User deletes connection configuration

```python
# Startup: Create preconfigured pools
for db_config in load_preconfigured_dbs():
    await pool_manager.create_pool(db_config)

# Runtime: Lazy pool creation
pool = await pool_manager.get_or_create_pool(db_id)

# Shutdown: Close all pools
await pool_manager.close_all()
```

### 3.3 Schema Cache Lifecycle

**Per-connection cache**: Schema cache is connection-specific, not pool-specific

**Invalidation strategy**:
1. **Automatic**: asyncpg detects stale cache on query error
2. **Manual**: Expose API to force schema reload for a database

```python
async def invalidate_schema_cache(pool: asyncpg.Pool) -> None:
    """Invalidate schema cache for all connections in pool."""
    async with pool.acquire() as conn:
        await conn.reload_schema_state()
    # Note: Other connections will invalidate lazily on error
```

---

## Transaction and Timeout Control

### 4.1 Timeout Parameters

#### statement_timeout
- **Purpose**: Abort any statement taking longer than specified time
- **Scope**: Cancels the current SQL statement, session continues
- **Recommended**: 30-60 seconds for interactive queries
- **Use case**: Prevents runaway queries from consuming resources

#### idle_in_transaction_session_timeout
- **Purpose**: Maximum time a session can be idle **inside a transaction**
- **Scope**: Terminates entire session, rolls back transaction
- **Recommended**: 60-120 seconds
- **Use case**: Prevents idle transactions from holding locks and blocking VACUUM

#### command_timeout (asyncpg-specific)
- **Purpose**: Timeout for acquiring connection and executing command
- **Scope**: Raises `asyncio.TimeoutError` on asyncpg side
- **Recommended**: 60 seconds
- **Use case**: Client-side timeout (independent of PostgreSQL)

### 4.2 Configuration Approach

**Method 1: Connection-level (Recommended)**

```python
pool = await asyncpg.create_pool(
    dsn,
    server_settings={
        "statement_timeout": "30000",  # 30 seconds (milliseconds)
        "idle_in_transaction_session_timeout": "60000",  # 60 seconds
    },
    command_timeout=60.0,  # asyncpg timeout
)
```

**Method 2: Session-level (Dynamic)**

```python
async with pool.acquire() as conn:
    await conn.execute("SET statement_timeout = '30s'")
    result = await conn.fetch("SELECT ...")
```

### 4.3 Transaction Isolation for Read-Only Queries

**Best practice**: Use `READ COMMITTED` isolation (PostgreSQL default)

```python
async with pool.acquire() as conn:
    async with conn.transaction(isolation="read_committed", readonly=True):
        result = await conn.fetch("SELECT * FROM large_table")
```

**Why readonly=True?**
- Prevents accidental writes
- PostgreSQL can optimize read-only transactions
- Explicit intent in code

### 4.4 Special Operations

**Disable timeouts for long-running maintenance**:

```python
async def run_pg_dump(conn: asyncpg.Connection):
    await conn.execute("SET statement_timeout = 0")  # Disable
    # Run pg_dump or other maintenance
```

---

## Error Handling Strategies

### 5.1 Error Categories

#### Connection Acquisition Errors

| Error | Cause | Handling |
|-------|-------|----------|
| `PoolTimeoutError` | Pool exhausted, `max_size` reached | Retry with exponential backoff |
| `PoolClosedError` | Pool was closed | Return HTTP 503, don't retry |
| `ConnectionRefusedError` | Database server unreachable | Log error, implement circuit breaker |

#### Query Execution Errors

| Error | Cause | Handling |
|-------|-------|----------|
| `PostgresSyntaxError` | Invalid SQL | Return error to user, don't retry |
| `InsufficientPrivilegeError` | Permission denied | Return error to user, don't retry |
| `QueryCanceledError` | `statement_timeout` exceeded | Return timeout error to user |
| `OutdatedSchemaCacheError` | Schema changed | Reload schema, retry once |
| `InvalidCachedStatementError` | Prepared statement invalid | asyncpg auto-clears cache, retry once |

#### Network Errors

| Error | Cause | Handling |
|-------|-------|----------|
| `ConnectionResetError` | Network interruption | Close connection, retry with new connection |
| `asyncio.TimeoutError` | `command_timeout` exceeded | Return timeout error to user |

### 5.2 Circuit Breaker Pattern

**Problem**: Pool exhaustion cascading failures

**Solution**: Circuit breaker with pybreaker

```python
from pybreaker import CircuitBreaker

# Create circuit breaker per database
db_breakers = {}

def get_breaker(db_id: str) -> CircuitBreaker:
    if db_id not in db_breakers:
        db_breakers[db_id] = CircuitBreaker(
            fail_max=5,  # Open circuit after 5 failures
            timeout_duration=60,  # Try again after 60 seconds
            exclude=[asyncpg.PostgresSyntaxError],  # Don't count user errors
        )
    return db_breakers[db_id]

# Usage
@get_breaker(db_id)
async def execute_query(pool, query):
    async with pool.acquire() as conn:
        return await conn.fetch(query)
```

### 5.3 Connection Leak Prevention

**Problem**: Forgetting to release connection causes pool exhaustion

**Solution**: Always use `async with` (context manager)

```python
# ✅ GOOD: Automatic release
async with pool.acquire() as conn:
    result = await conn.fetch("SELECT * FROM users")

# ❌ BAD: Manual release (error-prone)
conn = await pool.acquire()
try:
    result = await conn.fetch("SELECT * FROM users")
finally:
    await pool.release(conn)
```

**Monitoring**: Track acquire time histogram, alert on p95 > 100ms (Grafana)

### 5.4 Error Recovery Workflow

```python
async def execute_with_recovery(pool, query, max_retries=2):
    """Execute query with automatic error recovery."""

    for attempt in range(max_retries):
        try:
            async with pool.acquire(timeout=10.0) as conn:
                return await conn.fetch(query)

        except asyncpg.OutdatedSchemaCacheError:
            # Schema changed, reload and retry
            async with pool.acquire() as conn:
                await conn.reload_schema_state()
            continue

        except asyncpg.InvalidCachedStatementError:
            # Prepared statement invalid, cache auto-cleared, retry
            continue

        except asyncpg.PoolTimeoutError:
            if attempt == max_retries - 1:
                raise HTTPException(503, "Database pool exhausted")
            await asyncio.sleep(1.0 * (attempt + 1))
            continue

        except asyncpg.PostgresSyntaxError as e:
            # User error, don't retry
            raise HTTPException(400, f"Invalid SQL: {e}")

        except asyncpg.InsufficientPrivilegeError as e:
            # Permission error, don't retry
            raise HTTPException(403, f"Permission denied: {e}")

        except asyncpg.QueryCanceledError:
            # Timeout, don't retry
            raise HTTPException(408, "Query timeout exceeded")

        except (ConnectionResetError, asyncio.TimeoutError):
            # Network error, retry
            if attempt == max_retries - 1:
                raise HTTPException(503, "Database connection lost")
            await asyncio.sleep(2.0 * (attempt + 1))
            continue
```

---

## Architecture Design

### 6.1 Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         PoolManager                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  + create_pool(config: DBConfig) -> str                         │
│  + get_pool(db_id: str) -> Pool | None                          │
│  + get_or_create_pool(config: DBConfig) -> Pool                 │
│  + close_pool(db_id: str) -> None                               │
│  + close_all() -> None                                           │
│  + execute_query(db_id: str, query: str) -> List[Dict]          │
│  + get_pool_stats(db_id: str) -> PoolStats                      │
│  + invalidate_schema_cache(db_id: str) -> None                  │
│                                                                  │
│  - _pools: Dict[str, Pool]                                       │
│  - _pool_configs: Dict[str, DBConfig]                            │
│  - _last_used: Dict[str, datetime]                               │
│  - _lock: asyncio.Lock                                           │
│  - _background_tasks: Set[asyncio.Task]                          │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
                            │
                            │ manages
                            ▼
        ┌─────────────────────────────────────┐
        │      asyncpg.Pool (per database)    │
        ├─────────────────────────────────────┤
        │  - min_size: 5                      │
        │  - max_size: 20                     │
        │  - max_queries: 50000               │
        │  - max_inactive_connection: 300s    │
        │  - command_timeout: 60s             │
        └─────────────────────────────────────┘
                            │
                            │ acquires
                            ▼
        ┌─────────────────────────────────────┐
        │   asyncpg.Connection (per query)    │
        ├─────────────────────────────────────┤
        │  - Executes SQL queries             │
        │  - Manages transactions             │
        │  - Caches schema/prepared statements│
        └─────────────────────────────────────┘
```

### 6.2 Class Diagram

```python
@dataclass
class DBConfig:
    """Database connection configuration."""
    host: str
    port: int
    database: str
    user: str
    password: str
    ssl: bool = False
    pool_min_size: int = 5
    pool_max_size: int = 20
    statement_timeout: int = 30000  # milliseconds
    idle_timeout: int = 60000  # milliseconds

@dataclass
class PoolStats:
    """Connection pool statistics."""
    db_id: str
    size: int  # Current pool size
    free: int  # Available connections
    max_size: int
    min_size: int
    queries_executed: int
    avg_acquire_time_ms: float
    last_used: datetime

class PoolManager:
    """Manages multiple database connection pools."""

    def __init__(
        self,
        idle_pool_timeout: timedelta = timedelta(minutes=30),
        enable_monitoring: bool = True
    ):
        """Initialize pool manager."""

    async def create_pool(self, config: DBConfig) -> str:
        """Create a new connection pool."""

    async def get_pool(self, db_id: str) -> asyncpg.Pool | None:
        """Get existing pool by ID."""

    async def get_or_create_pool(self, config: DBConfig) -> asyncpg.Pool:
        """Get or create pool for database."""

    async def close_pool(self, db_id: str) -> None:
        """Close and remove a specific pool."""

    async def close_all(self) -> None:
        """Close all pools gracefully."""

    async def execute_query(
        self,
        db_id: str,
        query: str,
        timeout: float = 30.0,
        readonly: bool = True
    ) -> list[dict]:
        """Execute query with automatic error handling."""

    async def get_pool_stats(self, db_id: str) -> PoolStats:
        """Get connection pool statistics."""

    async def invalidate_schema_cache(self, db_id: str) -> None:
        """Force schema cache reload for database."""

    async def _cleanup_idle_pools(self) -> None:
        """Background task to close idle pools."""

    async def _monitor_pools(self) -> None:
        """Background task to collect metrics."""
```

### 6.3 Sequence Diagram: Query Execution

```
Client      API Route      PoolManager      asyncpg.Pool     PostgreSQL
  │             │               │                │                │
  ├─Query──────>│               │                │                │
  │             ├─execute_query─>               │                │
  │             │               ├─get_pool──────>│                │
  │             │               │<──pool─────────┤                │
  │             │               │                │                │
  │             │               ├─acquire────────>│                │
  │             │               │                ├─get_conn──────>│
  │             │               │                │<──conn─────────┤
  │             │               │<──conn─────────┤                │
  │             │               │                │                │
  │             │               ├─fetch(query)───────────────────>│
  │             │               │                │<──result───────┤
  │             │               │                │                │
  │             │               ├─release(conn)──>│                │
  │             │               │                ├─return_conn───>│
  │             │               │                │                │
  │             │<──result──────┤                │                │
  │<─Response───┤               │                │                │
```

---

## Implementation

### 7.1 Core Pool Manager

```python
"""
Connection pool manager for asyncpg.

Manages multiple database connection pools with automatic lifecycle,
error handling, and monitoring.
"""

import asyncio
import hashlib
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

import asyncpg
from pybreaker import CircuitBreaker

logger = logging.getLogger(__name__)


@dataclass
class DBConfig:
    """Database connection configuration."""

    host: str
    port: int
    database: str
    user: str
    password: str
    ssl: bool = False
    pool_min_size: int = 5
    pool_max_size: int = 20
    max_queries: int = 50000
    max_inactive_connection_lifetime: float = 300.0
    command_timeout: float = 60.0
    statement_timeout: int = 30000  # milliseconds
    idle_in_transaction_timeout: int = 60000  # milliseconds

    def to_pool_kwargs(self) -> dict[str, Any]:
        """Convert config to asyncpg.create_pool kwargs."""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
            "ssl": self.ssl,
            "min_size": self.pool_min_size,
            "max_size": self.pool_max_size,
            "max_queries": self.max_queries,
            "max_inactive_connection_lifetime": self.max_inactive_connection_lifetime,
            "command_timeout": self.command_timeout,
            "server_settings": {
                "statement_timeout": str(self.statement_timeout),
                "idle_in_transaction_session_timeout": str(
                    self.idle_in_transaction_timeout
                ),
            },
        }

    def get_id(self) -> str:
        """Generate unique ID for this database connection."""
        connection_string = f"{self.user}@{self.host}:{self.port}/{self.database}"
        return hashlib.sha256(connection_string.encode()).hexdigest()[:16]


@dataclass
class PoolStats:
    """Connection pool statistics."""

    db_id: str
    size: int
    free: int
    max_size: int
    min_size: int
    queries_executed: int = 0
    avg_acquire_time_ms: float = 0.0
    last_used: datetime = field(default_factory=datetime.now)


class PoolManager:
    """
    Manages multiple asyncpg connection pools.

    Features:
    - Independent pool per database
    - Automatic pool lifecycle management
    - Connection health monitoring
    - Schema cache invalidation
    - Circuit breaker pattern
    - Background cleanup of idle pools
    """

    def __init__(
        self,
        idle_pool_timeout: timedelta = timedelta(minutes=30),
        enable_monitoring: bool = True,
        enable_cleanup: bool = True,
    ):
        """
        Initialize pool manager.

        Args:
            idle_pool_timeout: Close pools idle for this duration
            enable_monitoring: Enable background metrics collection
            enable_cleanup: Enable automatic cleanup of idle pools
        """
        self._pools: dict[str, asyncpg.Pool] = {}
        self._pool_configs: dict[str, DBConfig] = {}
        self._last_used: dict[str, datetime] = {}
        self._circuit_breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()
        self._background_tasks: set[asyncio.Task] = set()
        self._idle_pool_timeout = idle_pool_timeout
        self._enable_monitoring = enable_monitoring
        self._enable_cleanup = enable_cleanup
        self._acquire_times: dict[str, list[float]] = defaultdict(list)
        self._query_counts: dict[str, int] = defaultdict(int)

        # Start background tasks
        if self._enable_cleanup:
            task = asyncio.create_task(self._cleanup_idle_pools())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

        if self._enable_monitoring:
            task = asyncio.create_task(self._monitor_pools())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

    async def create_pool(self, config: DBConfig) -> str:
        """
        Create a new connection pool.

        Args:
            config: Database configuration

        Returns:
            Database ID (unique identifier for this pool)

        Raises:
            ConnectionError: If pool creation fails
        """
        db_id = config.get_id()

        async with self._lock:
            if db_id in self._pools:
                logger.info(f"Pool {db_id} already exists, skipping creation")
                return db_id

            try:
                logger.info(
                    f"Creating pool for {config.database} on {config.host}:{config.port}"
                )
                pool = await asyncpg.create_pool(**config.to_pool_kwargs())
                self._pools[db_id] = pool
                self._pool_configs[db_id] = config
                self._last_used[db_id] = datetime.now()

                # Create circuit breaker for this database
                self._circuit_breakers[db_id] = CircuitBreaker(
                    fail_max=5,  # Open circuit after 5 consecutive failures
                    timeout_duration=60,  # Try again after 60 seconds
                    exclude=[
                        asyncpg.PostgresSyntaxError,
                        asyncpg.InsufficientPrivilegeError,
                    ],
                )

                logger.info(f"Pool {db_id} created successfully")
                return db_id

            except Exception as e:
                logger.error(f"Failed to create pool {db_id}: {e}")
                raise ConnectionError(f"Failed to create database pool: {e}") from e

    async def get_pool(self, db_id: str) -> asyncpg.Pool | None:
        """
        Get existing pool by ID.

        Args:
            db_id: Database identifier

        Returns:
            Pool instance or None if not found
        """
        return self._pools.get(db_id)

    async def get_or_create_pool(self, config: DBConfig) -> tuple[str, asyncpg.Pool]:
        """
        Get existing pool or create new one.

        Args:
            config: Database configuration

        Returns:
            Tuple of (db_id, pool)
        """
        db_id = config.get_id()
        pool = await self.get_pool(db_id)

        if pool is None:
            db_id = await self.create_pool(config)
            pool = self._pools[db_id]

        self._last_used[db_id] = datetime.now()
        return db_id, pool

    async def close_pool(self, db_id: str) -> None:
        """
        Close and remove a specific pool.

        Args:
            db_id: Database identifier
        """
        async with self._lock:
            pool = self._pools.pop(db_id, None)
            if pool is not None:
                logger.info(f"Closing pool {db_id}")
                await pool.close()
                self._pool_configs.pop(db_id, None)
                self._last_used.pop(db_id, None)
                self._circuit_breakers.pop(db_id, None)
                self._acquire_times.pop(db_id, None)
                self._query_counts.pop(db_id, None)

    async def close_all(self) -> None:
        """Close all pools and stop background tasks."""
        logger.info("Closing all connection pools")

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
        await asyncio.gather(*self._background_tasks, return_exceptions=True)

        # Close all pools
        async with self._lock:
            for db_id in list(self._pools.keys()):
                await self.close_pool(db_id)

        logger.info("All pools closed")

    async def execute_query(
        self,
        db_id: str,
        query: str,
        timeout: float = 30.0,
        readonly: bool = True,
        max_retries: int = 2,
    ) -> list[dict[str, Any]]:
        """
        Execute query with automatic error handling and retries.

        Args:
            db_id: Database identifier
            query: SQL query to execute
            timeout: Query timeout in seconds
            readonly: Whether query is read-only
            max_retries: Maximum retry attempts

        Returns:
            List of result rows as dictionaries

        Raises:
            ValueError: If pool not found
            TimeoutError: If query exceeds timeout
            PermissionError: If insufficient privileges
            Various asyncpg exceptions
        """
        pool = await self.get_pool(db_id)
        if pool is None:
            raise ValueError(f"Pool {db_id} not found")

        # Update last used timestamp
        self._last_used[db_id] = datetime.now()

        # Get circuit breaker for this database
        breaker = self._circuit_breakers[db_id]

        @breaker
        async def _execute():
            return await self._execute_with_recovery(
                pool, query, timeout, readonly, max_retries
            )

        return await _execute()

    async def _execute_with_recovery(
        self,
        pool: asyncpg.Pool,
        query: str,
        timeout: float,
        readonly: bool,
        max_retries: int,
    ) -> list[dict[str, Any]]:
        """Execute query with automatic error recovery."""
        for attempt in range(max_retries):
            try:
                # Track acquisition time
                start_time = asyncio.get_event_loop().time()

                async with pool.acquire(timeout=10.0) as conn:
                    acquire_time = (
                        asyncio.get_event_loop().time() - start_time
                    ) * 1000
                    db_id = list(self._pools.keys())[
                        list(self._pools.values()).index(pool)
                    ]
                    self._acquire_times[db_id].append(acquire_time)
                    self._query_counts[db_id] += 1

                    # Execute in transaction (read-only if specified)
                    async with conn.transaction(
                        isolation="read_committed", readonly=readonly
                    ):
                        result = await asyncio.wait_for(
                            conn.fetch(query), timeout=timeout
                        )
                        return [dict(row) for row in result]

            except asyncpg.OutdatedSchemaCacheError:
                logger.warning("Schema cache outdated, reloading")
                async with pool.acquire() as conn:
                    await conn.reload_schema_state()
                if attempt < max_retries - 1:
                    continue
                raise

            except asyncpg.InvalidCachedStatementError:
                logger.warning("Cached statement invalid, retrying")
                if attempt < max_retries - 1:
                    continue
                raise

            except asyncpg.PoolTimeoutError as e:
                logger.error(f"Pool exhausted (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    raise ConnectionError("Database pool exhausted") from e
                await asyncio.sleep(1.0 * (attempt + 1))
                continue

            except asyncpg.PostgresSyntaxError as e:
                logger.error(f"SQL syntax error: {e}")
                raise ValueError(f"Invalid SQL syntax: {e}") from e

            except asyncpg.InsufficientPrivilegeError as e:
                logger.error(f"Permission denied: {e}")
                raise PermissionError(f"Insufficient privileges: {e}") from e

            except asyncpg.QueryCanceledError as e:
                logger.error("Query canceled due to timeout")
                raise TimeoutError("Query timeout exceeded") from e

            except asyncio.TimeoutError as e:
                logger.error(f"Command timeout after {timeout}s")
                raise TimeoutError(f"Query timeout after {timeout}s") from e

            except (ConnectionResetError, OSError) as e:
                logger.error(
                    f"Network error (attempt {attempt + 1}/{max_retries}): {e}"
                )
                if attempt == max_retries - 1:
                    raise ConnectionError("Database connection lost") from e
                await asyncio.sleep(2.0 * (attempt + 1))
                continue

        raise RuntimeError("Max retries exceeded")

    async def get_pool_stats(self, db_id: str) -> PoolStats | None:
        """
        Get connection pool statistics.

        Args:
            db_id: Database identifier

        Returns:
            Pool statistics or None if pool not found
        """
        pool = await self.get_pool(db_id)
        if pool is None:
            return None

        # Calculate average acquire time
        acquire_times = self._acquire_times.get(db_id, [])
        avg_acquire_time = sum(acquire_times) / len(acquire_times) if acquire_times else 0.0

        return PoolStats(
            db_id=db_id,
            size=pool.get_size(),
            free=pool.get_idle_size(),
            max_size=pool.get_max_size(),
            min_size=pool.get_min_size(),
            queries_executed=self._query_counts.get(db_id, 0),
            avg_acquire_time_ms=avg_acquire_time,
            last_used=self._last_used.get(db_id, datetime.now()),
        )

    async def invalidate_schema_cache(self, db_id: str) -> None:
        """
        Force schema cache reload for database.

        Args:
            db_id: Database identifier

        Raises:
            ValueError: If pool not found
        """
        pool = await self.get_pool(db_id)
        if pool is None:
            raise ValueError(f"Pool {db_id} not found")

        logger.info(f"Invalidating schema cache for {db_id}")
        async with pool.acquire() as conn:
            await conn.reload_schema_state()

    async def _cleanup_idle_pools(self) -> None:
        """Background task to close idle pools."""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                now = datetime.now()
                idle_pools = []

                for db_id, last_used in self._last_used.items():
                    if now - last_used > self._idle_pool_timeout:
                        idle_pools.append(db_id)

                for db_id in idle_pools:
                    logger.info(f"Closing idle pool {db_id}")
                    await self.close_pool(db_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    async def _monitor_pools(self) -> None:
        """Background task to collect metrics."""
        while True:
            try:
                await asyncio.sleep(30)  # Monitor every 30 seconds

                for db_id in list(self._pools.keys()):
                    stats = await self.get_pool_stats(db_id)
                    if stats:
                        logger.debug(
                            f"Pool {db_id}: size={stats.size}/{stats.max_size}, "
                            f"free={stats.free}, queries={stats.queries_executed}, "
                            f"avg_acquire={stats.avg_acquire_time_ms:.2f}ms"
                        )

                        # Alert if pool is near exhaustion
                        if stats.free < 2 and stats.size >= stats.max_size:
                            logger.warning(
                                f"Pool {db_id} near exhaustion: "
                                f"free={stats.free}, size={stats.size}"
                            )

                        # Alert if acquire time is high
                        if stats.avg_acquire_time_ms > 100:
                            logger.warning(
                                f"Pool {db_id} slow acquire time: "
                                f"{stats.avg_acquire_time_ms:.2f}ms"
                            )

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring task: {e}")
```

### 7.2 Usage Example

```python
"""Example usage of PoolManager in FastAPI application."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

# Global pool manager
pool_manager: PoolManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global pool_manager

    # Startup: Create pool manager and preconfigured pools
    pool_manager = PoolManager(
        idle_pool_timeout=timedelta(minutes=30),
        enable_monitoring=True,
        enable_cleanup=True,
    )

    # Load preconfigured databases
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
        await pool_manager.create_pool(config)

    yield

    # Shutdown: Close all pools
    if pool_manager:
        await pool_manager.close_all()


app = FastAPI(lifespan=lifespan)


@app.post("/query")
async def execute_query(
    db_id: str,
    query: str,
    timeout: float = 30.0,
):
    """Execute SQL query on specified database."""
    try:
        result = await pool_manager.execute_query(
            db_id=db_id,
            query=query,
            timeout=timeout,
            readonly=True,
        )
        return {"rows": result, "count": len(result)}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except TimeoutError as e:
        raise HTTPException(status_code=408, detail=str(e))
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.post("/databases")
async def create_database_connection(config: DBConfig):
    """Create new database connection pool."""
    try:
        db_id = await pool_manager.create_pool(config)
        return {"db_id": db_id, "status": "created"}
    except ConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))


@app.get("/databases/{db_id}/stats")
async def get_pool_stats(db_id: str):
    """Get connection pool statistics."""
    stats = await pool_manager.get_pool_stats(db_id)
    if stats is None:
        raise HTTPException(status_code=404, detail="Database not found")
    return stats


@app.post("/databases/{db_id}/invalidate-cache")
async def invalidate_cache(db_id: str):
    """Force schema cache invalidation."""
    try:
        await pool_manager.invalidate_schema_cache(db_id)
        return {"status": "cache_invalidated"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.delete("/databases/{db_id}")
async def close_database_pool(db_id: str):
    """Close database connection pool."""
    await pool_manager.close_pool(db_id)
    return {"status": "closed"}
```

### 7.3 Testing Strategy

```python
"""Unit tests for PoolManager."""

import pytest
import asyncpg

from pool_manager import PoolManager, DBConfig


@pytest.fixture
async def pool_manager():
    """Create pool manager for testing."""
    manager = PoolManager(
        enable_monitoring=False,  # Disable for tests
        enable_cleanup=False,
    )
    yield manager
    await manager.close_all()


@pytest.fixture
def db_config():
    """Test database configuration."""
    return DBConfig(
        host="localhost",
        port=5432,
        database="test_db",
        user="test_user",
        password="test_pass",
    )


@pytest.mark.asyncio
async def test_create_pool(pool_manager, db_config):
    """Test pool creation."""
    db_id = await pool_manager.create_pool(db_config)
    assert db_id is not None
    assert await pool_manager.get_pool(db_id) is not None


@pytest.mark.asyncio
async def test_create_duplicate_pool(pool_manager, db_config):
    """Test creating duplicate pool returns same ID."""
    db_id1 = await pool_manager.create_pool(db_config)
    db_id2 = await pool_manager.create_pool(db_config)
    assert db_id1 == db_id2


@pytest.mark.asyncio
async def test_get_or_create_pool(pool_manager, db_config):
    """Test get_or_create creates pool on first call."""
    db_id1, pool1 = await pool_manager.get_or_create_pool(db_config)
    db_id2, pool2 = await pool_manager.get_or_create_pool(db_config)
    assert db_id1 == db_id2
    assert pool1 is pool2


@pytest.mark.asyncio
async def test_execute_query_success(pool_manager, db_config):
    """Test successful query execution."""
    db_id = await pool_manager.create_pool(db_config)
    result = await pool_manager.execute_query(db_id, "SELECT 1 AS value")
    assert len(result) == 1
    assert result[0]["value"] == 1


@pytest.mark.asyncio
async def test_execute_query_syntax_error(pool_manager, db_config):
    """Test query with syntax error."""
    db_id = await pool_manager.create_pool(db_config)
    with pytest.raises(ValueError, match="Invalid SQL syntax"):
        await pool_manager.execute_query(db_id, "SELECT INVALID")


@pytest.mark.asyncio
async def test_execute_query_timeout(pool_manager, db_config):
    """Test query timeout."""
    db_id = await pool_manager.create_pool(db_config)
    with pytest.raises(TimeoutError):
        await pool_manager.execute_query(
            db_id, "SELECT pg_sleep(60)", timeout=1.0
        )


@pytest.mark.asyncio
async def test_get_pool_stats(pool_manager, db_config):
    """Test retrieving pool statistics."""
    db_id = await pool_manager.create_pool(db_config)
    await pool_manager.execute_query(db_id, "SELECT 1")

    stats = await pool_manager.get_pool_stats(db_id)
    assert stats is not None
    assert stats.db_id == db_id
    assert stats.queries_executed >= 1
    assert stats.size >= db_config.pool_min_size


@pytest.mark.asyncio
async def test_invalidate_schema_cache(pool_manager, db_config):
    """Test schema cache invalidation."""
    db_id = await pool_manager.create_pool(db_config)
    await pool_manager.invalidate_schema_cache(db_id)
    # No exception = success


@pytest.mark.asyncio
async def test_close_pool(pool_manager, db_config):
    """Test closing specific pool."""
    db_id = await pool_manager.create_pool(db_config)
    await pool_manager.close_pool(db_id)
    assert await pool_manager.get_pool(db_id) is None


@pytest.mark.asyncio
async def test_close_all(pool_manager, db_config):
    """Test closing all pools."""
    await pool_manager.create_pool(db_config)
    await pool_manager.close_all()
    assert len(pool_manager._pools) == 0


@pytest.mark.asyncio
async def test_concurrent_queries(pool_manager, db_config):
    """Test concurrent query execution."""
    db_id = await pool_manager.create_pool(db_config)

    # Execute 20 concurrent queries (exceeds min_size)
    queries = [
        pool_manager.execute_query(db_id, "SELECT pg_sleep(0.1), 1 AS value")
        for _ in range(20)
    ]

    results = await asyncio.gather(*queries)
    assert len(results) == 20
    assert all(result[0]["value"] == 1 for result in results)
```

---

## References

### Official Documentation
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [PostgreSQL Timeout Documentation](https://www.postgresql.org/docs/current/runtime-config-client.html)

### Best Practices Articles
- Connection pool sizing for server applications
- Advanced pool implementation eliminates need for PgBouncer
- Statement timeout vs idle transaction timeout differences
- Connection pool exhaustion and retry strategies
- Schema cache invalidation in asyncpg

### Key Insights
- Pool configuration: min_size=5, max_size=20 typical for 10+ concurrent queries
- Each database requires independent pool (no connection switching)
- Built-in lifecycle management eliminates need for explicit health checks
- Circuit breaker pattern prevents cascading failures
- Always use context managers to prevent connection leaks
- Monitor acquire time p95, alert on >100ms

---

## Appendices

### A. Configuration Checklist

- [ ] Set `min_size` based on baseline concurrent load
- [ ] Set `max_size` based on peak load and DB `max_connections`
- [ ] Configure `statement_timeout` (30-60s for interactive queries)
- [ ] Configure `idle_in_transaction_session_timeout` (60-120s)
- [ ] Enable `max_inactive_connection_lifetime` (300s default)
- [ ] Set `max_queries` for connection recycling (50000 default)
- [ ] Implement circuit breaker for pool exhaustion
- [ ] Use `async with` for automatic connection release
- [ ] Monitor acquire time histogram (alert on p95 > 100ms)
- [ ] Implement graceful shutdown (close all pools)

### B. Troubleshooting Guide

| Symptom | Cause | Solution |
|---------|-------|----------|
| `PoolTimeoutError` | Pool exhausted | Increase `max_size` or optimize queries |
| Slow acquire time | High contention | Increase `max_size` or add more pools |
| Connection leaks | Missing `async with` | Always use context managers |
| `OutdatedSchemaCacheError` | Schema changed | Automatic reload, no action needed |
| High memory usage | Too many connections | Lower `max_size` or reduce `max_inactive_connection_lifetime` |
| Stale connections | Long-lived connections | Lower `max_inactive_connection_lifetime` |

### C. Performance Tuning

1. **Pool Size Optimization**
   - Start with `min_size=5, max_size=20`
   - Monitor acquire time and pool exhaustion
   - Increase `max_size` if p95 acquire time > 100ms
   - Decrease if connections are mostly idle

2. **Query Optimization**
   - Use prepared statements (automatic in asyncpg)
   - Set appropriate `statement_timeout`
   - Use read-only transactions for queries
   - Avoid long-running transactions

3. **Connection Management**
   - Keep `max_inactive_connection_lifetime` at 300s
   - Set `max_queries=50000` to recycle connections
   - Close idle pools after 30 minutes
   - Monitor and alert on pool metrics

### D. Security Considerations

1. **Password Management**
   - Never log passwords
   - Use environment variables or secret management
   - Consider PostgreSQL SSL/TLS certificates
   - Rotate credentials periodically

2. **SQL Injection Prevention**
   - Always use parameterized queries: `conn.fetch("SELECT * FROM users WHERE id = $1", user_id)`
   - Never concatenate user input into SQL
   - Validate input at application boundaries

3. **Least Privilege**
   - Use read-only database users for query tools
   - Grant minimum required permissions
   - Use separate credentials per application

---

**Document Version**: 1.0
**Last Updated**: 2026-01-28
**Author**: Claude (Anthropic)
**Review Status**: Ready for Implementation
