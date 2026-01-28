# Asyncpg Connection Pool Architecture Summary

**Date**: 2026-01-28
**Project**: Week5 - Multi-Database Query Tool
**Version**: 1.0

---

## Quick Reference

### Recommended Configuration

```python
POOL_CONFIG = {
    "min_size": 5,              # Baseline connections
    "max_size": 20,             # Peak concurrent load
    "max_queries": 50000,       # Recycle after 50k queries
    "max_inactive_connection_lifetime": 300.0,  # 5 minutes
    "command_timeout": 60.0,    # 60 seconds
    "statement_timeout": 30000, # 30 seconds (milliseconds)
    "idle_in_transaction_session_timeout": 60000,  # 60 seconds
}
```

### Key Design Decisions

1. **Independent Pools**: One pool per database (asyncpg doesn't support database switching)
2. **Pool Sizing**: `min_size=5, max_size=20` for 10+ concurrent queries
3. **Timeout Strategy**: 30s statement timeout, 60s idle transaction timeout
4. **Error Recovery**: Circuit breaker + exponential backoff retries
5. **Health Checks**: Built-in `max_inactive_connection_lifetime` (no explicit checks needed)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Application Layer                            │
│                     (FastAPI / Web Framework)                        │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  │ execute_query(db_id, sql)
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         PoolManager                                 │
├─────────────────────────────────────────────────────────────────────┤
│  Responsibilities:                                                  │
│  • Manage multiple database pools (one per database)                │
│  • Handle pool lifecycle (create, close, cleanup)                   │
│  • Execute queries with error recovery                              │
│  • Track statistics (acquire time, query count)                     │
│  • Invalidate schema cache                                          │
│  • Circuit breaker pattern                                          │
│  • Background monitoring and cleanup                                │
├─────────────────────────────────────────────────────────────────────┤
│  State:                                                             │
│  • _pools: Dict[str, asyncpg.Pool]                                  │
│  • _pool_configs: Dict[str, DBConfig]                               │
│  • _last_used: Dict[str, datetime]                                  │
│  • _circuit_breakers: Dict[str, CircuitBreaker]                     │
│  • _acquire_times: Dict[str, List[float]]                           │
│  • _query_counts: Dict[str, int]                                    │
└─────────────────────────────────┬───────────────────────────────────┘
                                  │
                                  │ manages
                                  ▼
        ┌──────────────────────────────────────────────┐
        │       asyncpg.Pool (per database)            │
        ├──────────────────────────────────────────────┤
        │  Configuration:                              │
        │  • min_size: 5 (always-ready connections)    │
        │  • max_size: 20 (peak concurrent load)       │
        │  • max_queries: 50000 (recycle threshold)    │
        │  • max_inactive_connection: 300s             │
        │  • command_timeout: 60s                      │
        │                                              │
        │  Behavior:                                   │
        │  • Automatically creates connections         │
        │  • Recycles connections after max_queries    │
        │  • Closes idle connections after 5 min       │
        │  • Validates connections on acquire          │
        └──────────────────┬───────────────────────────┘
                          │
                          │ acquires/releases
                          ▼
        ┌──────────────────────────────────────────────┐
        │     asyncpg.Connection (per query)           │
        ├──────────────────────────────────────────────┤
        │  • Executes SQL queries                      │
        │  • Manages transactions                      │
        │  • Caches prepared statements                │
        │  • Caches schema metadata                    │
        │  • Handles error recovery                    │
        └──────────────────┬───────────────────────────┘
                          │
                          │ executes
                          ▼
        ┌──────────────────────────────────────────────┐
        │          PostgreSQL Database                 │
        └──────────────────────────────────────────────┘
```

---

## Component Responsibilities

### 1. PoolManager

**Purpose**: Central manager for all database connection pools

**Key Methods**:
- `create_pool(config)`: Create new pool for database
- `get_or_create_pool(config)`: Get existing or create new pool
- `execute_query(db_id, query)`: Execute query with error recovery
- `get_pool_stats(db_id)`: Retrieve pool statistics
- `invalidate_schema_cache(db_id)`: Force schema reload
- `close_pool(db_id)`: Close specific pool
- `close_all()`: Graceful shutdown

**Background Tasks**:
- `_cleanup_idle_pools()`: Close pools idle > 30 minutes
- `_monitor_pools()`: Collect metrics, alert on issues

### 2. asyncpg.Pool

**Purpose**: Manage connection lifecycle for a single database

**Features**:
- Connection pooling (min/max size)
- Automatic connection recycling
- Idle connection cleanup
- Connection validation
- Statement cache management

**Parameters**:
- `min_size`: Baseline connections (always maintained)
- `max_size`: Maximum concurrent connections
- `max_queries`: Recycle connection after N queries
- `max_inactive_connection_lifetime`: Close idle connections after N seconds
- `command_timeout`: Timeout for connection operations

### 3. asyncpg.Connection

**Purpose**: Execute queries and manage transactions

**Features**:
- Query execution (`fetch`, `fetchrow`, `execute`)
- Transaction management (`transaction()`)
- Prepared statement caching
- Schema metadata caching
- Notification listeners

**Lifecycle**:
- Acquired from pool via `async with pool.acquire()`
- Used for query execution
- Automatically released back to pool on context exit
- Reset on release (close cursors, transactions)

---

## Query Execution Flow

```
┌─────────┐
│ Client  │
└────┬────┘
     │
     │ 1. POST /query/{db_id}
     ▼
┌─────────────────┐
│  FastAPI Route  │
└────┬────────────┘
     │
     │ 2. pool_manager.execute_query(db_id, sql)
     ▼
┌──────────────────────┐
│    PoolManager       │
│  ┌────────────────┐  │
│  │ Circuit Breaker│  │  3. Check circuit state
│  └────────────────┘  │
└────┬─────────────────┘
     │
     │ 4. get_pool(db_id)
     ▼
┌──────────────────────┐
│   asyncpg.Pool       │
└────┬─────────────────┘
     │
     │ 5. pool.acquire(timeout=10s)
     ▼
┌──────────────────────┐
│  asyncpg.Connection  │
│                      │
│  ┌────────────────┐  │
│  │  Transaction   │  │  6. Begin read-only transaction
│  │  (READ COMMIT) │  │
│  └────────────────┘  │
└────┬─────────────────┘
     │
     │ 7. conn.fetch(sql)
     ▼
┌──────────────────────┐
│   PostgreSQL         │
│                      │
│  • Parse SQL         │
│  • Execute query     │
│  • Return results    │
└────┬─────────────────┘
     │
     │ 8. Results
     ▼
┌──────────────────────┐
│  asyncpg.Connection  │
│                      │
│  • Format results    │
│  • Commit transaction│
└────┬─────────────────┘
     │
     │ 9. Release connection
     ▼
┌──────────────────────┐
│   asyncpg.Pool       │
│                      │
│  • Reset connection  │
│  • Return to pool    │
└────┬─────────────────┘
     │
     │ 10. Return results
     ▼
┌──────────────────────┐
│   PoolManager        │
│                      │
│  • Track metrics     │
│  • Update last_used  │
└────┬─────────────────┘
     │
     │ 11. HTTP 200 + results
     ▼
┌─────────┐
│ Client  │
└─────────┘
```

---

## Error Handling Strategy

### Error Classification

| Error Type | Severity | Retry | Circuit Breaker |
|------------|----------|-------|-----------------|
| `PostgresSyntaxError` | User | No | Excluded |
| `InsufficientPrivilegeError` | User | No | Excluded |
| `QueryCanceledError` | Timeout | No | No |
| `PoolTimeoutError` | Resource | Yes | Yes |
| `OutdatedSchemaCacheError` | Recoverable | Yes | No |
| `InvalidCachedStatementError` | Recoverable | Yes | No |
| `ConnectionResetError` | Network | Yes | Yes |
| `asyncio.TimeoutError` | Timeout | No | No |

### Recovery Workflow

```
┌─────────────────┐
│ Execute Query   │
└────┬────────────┘
     │
     ▼
┌─────────────────────────┐
│ Check Circuit Breaker   │
└────┬────────────────────┘
     │
     ▼
┌─────────────────────────┐
│ Acquire Connection      │
│ (timeout=10s)           │
└────┬────────────────────┘
     │
     │ PoolTimeoutError?
     ├─────Yes────> Retry with exponential backoff (3x)
     │                    │
     │                    └──> Still failing? ──> Circuit OPEN
     │
     │ Network Error?
     ├─────Yes────> Retry with exponential backoff (2x)
     │
     │ OutdatedSchemaCacheError?
     ├─────Yes────> Reload schema, retry once
     │
     │ InvalidCachedStatementError?
     ├─────Yes────> Cache auto-cleared, retry once
     │
     │ Syntax/Permission Error?
     ├─────Yes────> Return error to user (don't retry)
     │
     ▼
┌─────────────────────────┐
│ Return Result           │
└─────────────────────────┘
```

---

## Multi-Database Pool Management

### Design Pattern: Independent Pools

```python
# BAD: Single shared pool (not supported by asyncpg)
pool = create_pool(host="server")  # Can't switch databases

# GOOD: Independent pools per database
pools = {
    "db1_id": create_pool(host="server", database="db1"),
    "db2_id": create_pool(host="server", database="db2"),
    "db3_id": create_pool(host="server", database="db3"),
}
```

### Pool Lifecycle

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Startup                      │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Create PoolManager           │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Load Preconfigured DBs       │
        │  (from config file/env)       │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Create Pool for Each DB      │
        └───────────────┬───────────────┘
                        │
                        ▼
┌───────────────────────────────────────────────────────────┐
│                 Runtime Operations                        │
│                                                           │
│  User Request ────> Get/Create Pool ────> Execute Query  │
│                                                           │
│  Dynamic DB ──────> Create New Pool ────> Execute Query  │
│                                                           │
│  Idle Pool ──────> Cleanup Task ────────> Close Pool     │
└───────────────────────┬───────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Application Shutdown         │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Cancel Background Tasks      │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Close All Pools              │
        │  (graceful shutdown)          │
        └───────────────────────────────┘
```

### Pool Cleanup Strategy

**Trigger**: Pool idle for > 30 minutes (configurable)

**Process**:
1. Background task checks every 60 seconds
2. Compare `last_used` timestamp with current time
3. If `now - last_used > idle_timeout`, close pool
4. Free resources (connections, memory)

**Exceptions**: Never close pools with active connections

---

## Performance Optimization

### 1. Pool Size Tuning

**Formula**:
```
min_size = max(2, concurrent_queries_baseline / num_databases)
max_size = min_size * 2 to 4 (burst capacity)
```

**Example** (10 concurrent queries, 3 databases):
```
min_size = max(2, 10 / 3) = 4
max_size = 4 * 2.5 = 10
```

### 2. Monitoring Metrics

**Key Metrics**:
- Pool size utilization: `current_size / max_size`
- Free connections: `free_connections / current_size`
- Acquire time p95: Alert if > 100ms
- Query count: Track total queries per pool
- Pool exhaustion rate: Count `PoolTimeoutError`

**Alerting Rules**:
```python
if pool.free < 2 and pool.size == pool.max_size:
    alert("Pool near exhaustion")

if avg_acquire_time_ms > 100:
    alert("Slow connection acquisition")

if circuit_breaker.state == "open":
    alert("Circuit breaker opened for database")
```

### 3. Connection Recycling

**Why**: Prevent connection degradation (memory leaks, stale state)

**Strategy**:
- `max_queries=50000`: Recycle after 50k queries
- `max_inactive_connection_lifetime=300`: Close idle connections after 5 min

**Benefits**:
- Fresh connections regularly
- Prevent PostgreSQL connection bloat
- Automatic recovery from transient issues

---

## Security Considerations

### 1. Password Management

```python
# BAD: Hardcoded passwords
config = DBConfig(password="secret123")

# GOOD: Environment variables
import os
config = DBConfig(password=os.getenv("DB_PASSWORD"))

# BETTER: Secret management service
from secret_manager import get_secret
config = DBConfig(password=get_secret("db-password"))
```

### 2. SQL Injection Prevention

```python
# BAD: String concatenation
query = f"SELECT * FROM users WHERE id = {user_id}"

# GOOD: Parameterized queries
query = "SELECT * FROM users WHERE id = $1"
result = await conn.fetch(query, user_id)
```

### 3. Least Privilege

```python
# Read-only user for query tool
config = DBConfig(
    user="readonly_user",
    password=get_secret("readonly-password"),
)

# Grant minimum permissions
# GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_user;
```

---

## Testing Strategy

### 1. Unit Tests

**Coverage**: All PoolManager methods

**Approach**:
- Mock asyncpg.Pool for isolated tests
- Test error handling with exception injection
- Verify retry logic with controlled failures

### 2. Integration Tests

**Coverage**: Real PostgreSQL connections

**Setup**:
```bash
docker run -d --name test-postgres \
    -e POSTGRES_PASSWORD=test \
    -e POSTGRES_DB=test_db \
    -p 5432:5432 \
    postgres:15
```

**Tests**:
- Pool creation and connection
- Query execution (SELECT, timeout)
- Concurrent queries (pool growth)
- Error scenarios (syntax error, timeout)

### 3. Load Tests

**Coverage**: Pool exhaustion, performance

**Tools**: locust, k6, or custom asyncio script

**Scenarios**:
- 50 concurrent users, 10 queries/user
- Pool exhaustion (exceed max_size)
- Long-running queries (test timeout)

---

## Deployment Checklist

- [ ] Configure pool sizes based on expected load
- [ ] Set appropriate timeouts (statement, idle)
- [ ] Enable monitoring and alerting
- [ ] Implement circuit breaker
- [ ] Use environment variables for passwords
- [ ] Configure graceful shutdown
- [ ] Test connection to all databases
- [ ] Verify PostgreSQL `max_connections` limit
- [ ] Set up logging (INFO for production)
- [ ] Document database connection strings
- [ ] Create health check endpoint
- [ ] Test failover/reconnection scenarios

---

## Additional Resources

### Documentation
- [asyncpg Documentation](https://magicstack.github.io/asyncpg/)
- [PostgreSQL Connection Pooling](https://www.postgresql.org/docs/current/runtime-config-connection.html)

### Implementation Files
- `VibeCoding/Week5/examples/pool_manager.py`: Complete implementation
- `VibeCoding/Week5/examples/fastapi_integration.py`: FastAPI example
- `VibeCoding/Week5/examples/test_pool_manager.py`: Unit tests

### Research
- `VibeCoding/Week5/research/asyncpg_connection_pool_best_practices.md`: Detailed research

---

**Last Updated**: 2026-01-28
**Version**: 1.0
**Status**: Ready for Implementation
