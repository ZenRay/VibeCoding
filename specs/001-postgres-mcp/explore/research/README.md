# Asyncpg Connection Pool Research - Week5

**Research Date**: 2026-01-28
**Project**: Multi-Database Query Tool
**Status**: Complete - Ready for Implementation

---

## Overview

This research provides comprehensive guidance for implementing asyncpg connection pool management for a multi-database PostgreSQL query tool supporting 10+ concurrent queries.

---

## Research Documents

### 1. Best Practices Guide (Primary Reference)

**File**: `asyncpg_connection_pool_best_practices.md`

**Contents**:
- Executive summary with key findings
- Connection pool configuration (sizing, parameters)
- Health checks and reconnection strategies
- Multi-database pool management architecture
- Transaction and timeout control
- Error handling strategies
- Complete implementation with tests

**When to use**: Primary reference for all implementation decisions

### 2. Architecture Summary (Quick Reference)

**File**: `asyncpg_architecture_summary.md`

**Contents**:
- Component diagrams
- Query execution flow
- Error handling workflows
- Multi-database lifecycle
- Performance optimization
- Security considerations
- Deployment checklist

**When to use**: Quick reference for architecture decisions and diagrams

### 3. Implementation Guide (Step-by-Step)

**File**: `implementation_guide.md`

**Contents**:
- Step-by-step setup instructions
- Configuration examples
- Testing procedures
- Production deployment
- Common patterns
- Troubleshooting guide

**When to use**: Follow this guide for implementation

---

## Implementation Files

### Core Implementation

**Location**: `/home/ray/Documents/VibeCoding/Week5/examples/`

| File | Description | LOC |
|------|-------------|-----|
| `pool_manager.py` | Complete PoolManager implementation | ~400 |
| `fastapi_integration.py` | FastAPI integration example | ~200 |
| `test_pool_manager.py` | Comprehensive unit tests | ~500 |

### Usage

```bash
# Copy to your project
cp examples/pool_manager.py src/pool/
cp examples/fastapi_integration.py src/
cp examples/test_pool_manager.py tests/
```

---

## Key Findings Summary

### 1. Pool Configuration

**Recommended for 10+ concurrent queries**:

```python
DBConfig(
    host="localhost",
    port=5432,
    database="mydb",
    user="postgres",
    password="secret",
    pool_min_size=5,              # Baseline connections
    pool_max_size=20,             # Peak load
    max_queries=50000,            # Recycle threshold
    max_inactive_connection_lifetime=300.0,  # 5 minutes
    command_timeout=60.0,         # 60 seconds
    statement_timeout=30000,      # 30 seconds (milliseconds)
    idle_in_transaction_timeout=60000,  # 60 seconds
)
```

### 2. Architecture Decision

**Independent Pools per Database**: asyncpg doesn't support database switching, so each database requires its own pool.

```python
pools = {
    "db1_id": Pool(host=..., database="db1"),
    "db2_id": Pool(host=..., database="db2"),
    "db3_id": Pool(host=..., database="db3"),
}
```

### 3. Error Handling

**Circuit Breaker Pattern**: Prevent cascading failures

```python
CircuitBreaker(
    fail_max=5,              # Open after 5 failures
    timeout_duration=60,     # Try again after 60s
    exclude=[SyntaxError],   # Don't count user errors
)
```

### 4. Health Checks

**Built-in Lifecycle Management**: No explicit health checks needed

```python
max_inactive_connection_lifetime=300.0  # Auto-close idle connections
max_queries=50000                       # Auto-recycle connections
```

### 5. Schema Cache

**Automatic Invalidation**: asyncpg handles cache invalidation on schema changes

```python
try:
    result = await conn.fetch(query)
except OutdatedSchemaCacheError:
    await conn.reload_schema_state()  # Auto-reload
    result = await conn.fetch(query)  # Retry
```

---

## Quick Start

### 1. Install Dependencies

```bash
uv pip install asyncpg pybreaker fastapi uvicorn
```

### 2. Start Test Database

```bash
docker run -d --name test-postgres \
    -e POSTGRES_PASSWORD=test \
    -p 5432:5432 \
    postgres:15
```

### 3. Run Example

```python
from pool_manager import PoolManager, DBConfig

manager = PoolManager()
config = DBConfig(host="localhost", port=5432, database="postgres", ...)
db_id = await manager.create_pool(config)
result = await manager.execute_query(db_id, "SELECT 1")
```

### 4. Run Tests

```bash
pytest examples/test_pool_manager.py -v
```

---

## Performance Characteristics

### Connection Pool

- **Baseline**: 5 connections (always ready)
- **Peak**: 20 connections (burst capacity)
- **Latency**: 10-100x faster than creating new connections
- **Acquire time**: < 10ms typical, alert if > 100ms

### Concurrent Queries

- **Supported**: 10+ concurrent queries per database
- **Scaling**: Pool automatically grows from min_size to max_size
- **Isolation**: Read-committed transaction isolation

### Resource Management

- **Connection recycling**: After 50,000 queries
- **Idle timeout**: 5 minutes
- **Pool cleanup**: 30 minutes idle time

---

## Security Best Practices

1. **Never log passwords**: Redact credentials from logs
2. **Use environment variables**: Store passwords securely
3. **Parameterized queries**: Always use `$1, $2` placeholders
4. **Least privilege**: Use read-only database users
5. **SSL/TLS**: Enable encryption for production

---

## Production Checklist

- [ ] Configure pool sizes based on load
- [ ] Set appropriate timeouts
- [ ] Enable monitoring and alerts
- [ ] Implement circuit breaker
- [ ] Use environment variables for passwords
- [ ] Configure SSL/TLS
- [ ] Test connection to all databases
- [ ] Verify PostgreSQL max_connections
- [ ] Set up logging (INFO level)
- [ ] Create health check endpoint
- [ ] Test graceful shutdown
- [ ] Document connection strings

---

## Monitoring and Alerts

### Key Metrics

```python
# Pool utilization
utilization = (pool.size - pool.free) / pool.max_size * 100

# Connection acquisition time
if avg_acquire_time_ms > 100:
    alert("Slow connection acquisition")

# Pool exhaustion
if pool.free < 2 and pool.size == pool.max_size:
    alert("Pool near exhaustion")
```

### Endpoints

```python
GET /metrics/{db_id}      # Pool statistics
GET /metrics              # All pools
GET /health               # Health check
```

---

## Common Issues and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| PoolTimeoutError | Pool exhausted | Increase max_size or optimize queries |
| High acquire time | Pool contention | Increase min_size |
| Connection leaks | Missing async with | Always use context managers |
| Stale schema cache | ALTER TABLE | Automatic reload (no action needed) |

---

## References

### Web Sources

- [asyncpg Connection Pool Configuration Best Practices](https://magicstack.github.io/asyncpg/)
- [PostgreSQL Timeout Parameters](https://www.postgresql.org/docs/current/runtime-config-client.html)
- Circuit Breaker Pattern with pybreaker
- Pool exhaustion and retry strategies

### Local Files

- `asyncpg_connection_pool_best_practices.md`: Detailed research (9,000+ words)
- `asyncpg_architecture_summary.md`: Architecture diagrams and flows
- `implementation_guide.md`: Step-by-step implementation
- `examples/pool_manager.py`: Production-ready implementation
- `examples/fastapi_integration.py`: FastAPI integration
- `examples/test_pool_manager.py`: Comprehensive tests

---

## Next Steps

1. **Review research documents**: Start with `asyncpg_connection_pool_best_practices.md`
2. **Study architecture**: Review `asyncpg_architecture_summary.md`
3. **Follow implementation guide**: Step-by-step in `implementation_guide.md`
4. **Copy implementation**: Use `examples/pool_manager.py` as foundation
5. **Write tests**: Adapt `examples/test_pool_manager.py` for your use cases
6. **Deploy**: Follow production checklist

---

## Contact and Support

**Research Completed By**: Claude (Anthropic)
**Date**: 2026-01-28
**Project**: Week5 Multi-Database Query Tool
**Status**: Production Ready

For questions or issues with this research, refer to:
- asyncpg documentation: https://magicstack.github.io/asyncpg/
- PostgreSQL documentation: https://www.postgresql.org/docs/

---

**Version**: 1.0
**Last Updated**: 2026-01-28
