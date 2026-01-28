# Asyncpg Connection Pool - Implementation Guide

**Quick Start Guide for Week5 Multi-Database Query Tool**

---

## Step 1: Install Dependencies

```bash
cd ~/Documents/VibeCoding/Week5

# Activate virtual environment
source .venv/bin/activate

# Install asyncpg and dependencies
uv pip install asyncpg pybreaker fastapi uvicorn pytest pytest-asyncio

# Or add to pyproject.toml:
# [project]
# dependencies = [
#     "asyncpg>=0.29.0",
#     "pybreaker>=1.0.2",
#     "fastapi>=0.104.0",
#     "uvicorn[standard]>=0.24.0",
# ]
# [project.optional-dependencies]
# dev = [
#     "pytest>=7.4.0",
#     "pytest-asyncio>=0.21.0",
# ]
```

---

## Step 2: Copy Implementation Files

```bash
# Create source directory
mkdir -p ~/Documents/VibeCoding/Week5/src/pool

# Copy pool manager implementation
cp ~/Documents/VibeCoding/Week5/examples/pool_manager.py \
   ~/Documents/VibeCoding/Week5/src/pool/

# Copy FastAPI integration
cp ~/Documents/VibeCoding/Week5/examples/fastapi_integration.py \
   ~/Documents/VibeCoding/Week5/src/

# Copy tests
mkdir -p ~/Documents/VibeCoding/Week5/tests
cp ~/Documents/VibeCoding/Week5/examples/test_pool_manager.py \
   ~/Documents/VibeCoding/Week5/tests/
```

---

## Step 3: Set Up PostgreSQL for Testing

### Option A: Docker (Recommended)

```bash
# Start PostgreSQL container
docker run -d --name week5-postgres \
    -e POSTGRES_PASSWORD=test \
    -e POSTGRES_DB=test_db \
    -p 5432:5432 \
    postgres:15

# Verify connection
docker exec -it week5-postgres psql -U postgres -d test_db -c "SELECT version();"
```

### Option B: Local PostgreSQL

```bash
# Create test database
createdb test_db

# Create test user
psql -c "CREATE USER test_user WITH PASSWORD 'test';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE test_db TO test_user;"
```

---

## Step 4: Basic Usage

### 4.1 Standalone Usage

```python
import asyncio
from pool_manager import PoolManager, DBConfig

async def main():
    # Create pool manager
    manager = PoolManager()

    # Configure database
    config = DBConfig(
        host="localhost",
        port=5432,
        database="test_db",
        user="postgres",
        password="test",
    )

    # Create pool
    db_id = await manager.create_pool(config)
    print(f"Created pool: {db_id}")

    # Execute query
    result = await manager.execute_query(db_id, "SELECT 1 AS value")
    print(f"Result: {result}")

    # Get statistics
    stats = await manager.get_pool_stats(db_id)
    print(f"Pool stats: {stats}")

    # Cleanup
    await manager.close_all()

if __name__ == "__main__":
    asyncio.run(main())
```

### 4.2 FastAPI Integration

```python
# File: src/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pool_manager import PoolManager, DBConfig

pool_manager: PoolManager | None = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool_manager

    # Startup
    pool_manager = PoolManager()

    # Create preconfigured pools
    config = DBConfig(
        host="localhost",
        port=5432,
        database="myapp",
        user="postgres",
        password="secret",
    )
    await pool_manager.create_pool(config)

    yield

    # Shutdown
    await pool_manager.close_all()

app = FastAPI(lifespan=lifespan)

@app.post("/query/{db_id}")
async def query(db_id: str, sql: str):
    result = await pool_manager.execute_query(db_id, sql)
    return {"rows": result, "count": len(result)}

# Run with: uvicorn main:app --reload
```

---

## Step 5: Configuration

### 5.1 Environment Variables

```bash
# Create .env file
cat > .env << EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=myapp
DB_USER=postgres
DB_PASSWORD=secret

POOL_MIN_SIZE=5
POOL_MAX_SIZE=20
POOL_IDLE_TIMEOUT=1800  # 30 minutes
EOF
```

### 5.2 Load Configuration

```python
import os
from dotenv import load_dotenv
from pool_manager import DBConfig

load_dotenv()

config = DBConfig(
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT")),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    pool_min_size=int(os.getenv("POOL_MIN_SIZE", "5")),
    pool_max_size=int(os.getenv("POOL_MAX_SIZE", "20")),
)
```

---

## Step 6: Run Tests

```bash
# Run all tests
pytest tests/test_pool_manager.py -v

# Run specific test
pytest tests/test_pool_manager.py::test_create_pool -v

# Run with coverage
pytest tests/test_pool_manager.py --cov=src/pool --cov-report=html

# Run integration tests only
pytest tests/test_pool_manager.py -v -m integration

# Skip integration tests
pytest tests/test_pool_manager.py -v -m "not integration"
```

---

## Step 7: Monitoring and Metrics

### 7.1 Enable Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Create pool manager with monitoring
manager = PoolManager(
    enable_monitoring=True,  # Enable background metrics
    enable_cleanup=True,     # Enable idle pool cleanup
)
```

### 7.2 Metrics Endpoint

```python
@app.get("/metrics/{db_id}")
async def get_metrics(db_id: str):
    stats = await pool_manager.get_pool_stats(db_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Pool not found")

    return {
        "db_id": stats.db_id,
        "pool_size": stats.size,
        "free_connections": stats.free,
        "utilization": (stats.size - stats.free) / stats.size * 100,
        "queries_executed": stats.queries_executed,
        "avg_acquire_time_ms": stats.avg_acquire_time_ms,
        "last_used": stats.last_used.isoformat(),
    }

@app.get("/metrics")
async def get_all_metrics():
    metrics = []
    for db_id in pool_manager._pools.keys():
        stats = await pool_manager.get_pool_stats(db_id)
        if stats:
            metrics.append(stats)
    return {"pools": metrics, "count": len(metrics)}
```

---

## Step 8: Production Deployment

### 8.1 Configuration Checklist

```python
# Production configuration
production_config = DBConfig(
    host="prod-db.example.com",
    port=5432,
    database="production",
    user="app_user",
    password=os.getenv("DB_PASSWORD"),  # From secret manager
    ssl=True,  # Enable SSL/TLS
    pool_min_size=10,  # Higher baseline for production
    pool_max_size=50,  # Handle burst traffic
    max_queries=50000,
    max_inactive_connection_lifetime=300.0,
    command_timeout=60.0,
    statement_timeout=30000,  # 30 seconds
    idle_in_transaction_timeout=60000,  # 60 seconds
)
```

### 8.2 Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    """Check application and database health."""
    try:
        # Check each pool
        healthy_pools = 0
        total_pools = len(pool_manager._pools)

        for db_id in pool_manager._pools.keys():
            try:
                # Simple query to verify connection
                await pool_manager.execute_query(
                    db_id,
                    "SELECT 1",
                    timeout=5.0,
                )
                healthy_pools += 1
            except Exception:
                pass

        status = "healthy" if healthy_pools == total_pools else "degraded"

        return {
            "status": status,
            "pools": {
                "total": total_pools,
                "healthy": healthy_pools,
            },
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }
```

### 8.3 Graceful Shutdown

```python
import signal
import asyncio

def handle_shutdown(signum, frame):
    """Handle shutdown signals."""
    asyncio.create_task(shutdown())

async def shutdown():
    """Graceful shutdown procedure."""
    logger.info("Shutting down...")

    # Close all pools
    if pool_manager:
        await pool_manager.close_all()

    logger.info("Shutdown complete")

# Register signal handlers
signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)
```

---

## Step 9: Common Patterns

### 9.1 Multiple Database Queries

```python
async def query_multiple_databases(query: str, db_ids: list[str]):
    """Execute same query across multiple databases."""
    tasks = [
        pool_manager.execute_query(db_id, query)
        for db_id in db_ids
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Separate successes and failures
    successes = []
    failures = []

    for db_id, result in zip(db_ids, results):
        if isinstance(result, Exception):
            failures.append({"db_id": db_id, "error": str(result)})
        else:
            successes.append({"db_id": db_id, "rows": result})

    return {"successes": successes, "failures": failures}
```

### 9.2 Dynamic Database Connection

```python
@app.post("/databases/connect")
async def connect_database(config: DBConfig):
    """Dynamically connect to new database."""
    try:
        db_id, pool = await pool_manager.get_or_create_pool(config)

        # Test connection
        await pool_manager.execute_query(db_id, "SELECT 1")

        return {
            "db_id": db_id,
            "status": "connected",
        }

    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect: {e}",
        )
```

### 9.3 Query with Parameters

```python
async def query_with_params(db_id: str, table: str, user_id: int):
    """Execute parameterized query (safe from SQL injection)."""
    pool = await pool_manager.get_pool(db_id)

    async with pool.acquire() as conn:
        # Use $1, $2 for parameters (NOT string formatting)
        query = "SELECT * FROM {} WHERE user_id = $1".format(table)
        result = await conn.fetch(query, user_id)
        return [dict(row) for row in result]
```

---

## Step 10: Troubleshooting

### Common Issues

#### 1. PoolTimeoutError

**Symptom**: `asyncpg.PoolTimeoutError: timeout acquiring a connection`

**Causes**:
- Pool too small for load
- Connections not being released
- Long-running queries

**Solutions**:
```python
# Increase pool size
config.pool_max_size = 50

# Check connection leaks (always use async with)
async with pool.acquire() as conn:
    result = await conn.fetch(query)

# Reduce query timeout
await manager.execute_query(db_id, query, timeout=10.0)
```

#### 2. High Acquire Time

**Symptom**: Slow connection acquisition (>100ms)

**Causes**:
- Pool contention
- Network latency
- Database overload

**Solutions**:
```python
# Increase min_size for ready connections
config.pool_min_size = 10

# Monitor acquire time
stats = await manager.get_pool_stats(db_id)
if stats.avg_acquire_time_ms > 100:
    logger.warning(f"Slow acquire: {stats.avg_acquire_time_ms}ms")
```

#### 3. Connection Refused

**Symptom**: `ConnectionRefusedError: Connection refused`

**Causes**:
- Database not running
- Wrong host/port
- Firewall blocking connection

**Solutions**:
```bash
# Test connection manually
psql -h localhost -p 5432 -U postgres -d test_db

# Check database is running
docker ps | grep postgres

# Check network
telnet localhost 5432
```

---

## Next Steps

1. **Implement in your project**: Copy files to your source directory
2. **Configure databases**: Update connection settings
3. **Write tests**: Create tests for your specific use cases
4. **Set up monitoring**: Add metrics and alerts
5. **Deploy**: Follow production deployment checklist

---

## Reference Files

- **Implementation**: `/home/ray/Documents/VibeCoding/Week5/examples/pool_manager.py`
- **FastAPI Example**: `/home/ray/Documents/VibeCoding/Week5/examples/fastapi_integration.py`
- **Tests**: `/home/ray/Documents/VibeCoding/Week5/examples/test_pool_manager.py`
- **Research**: `/home/ray/Documents/VibeCoding/Week5/research/asyncpg_connection_pool_best_practices.md`
- **Architecture**: `/home/ray/Documents/VibeCoding/Week5/research/asyncpg_architecture_summary.md`

---

**Last Updated**: 2026-01-28
**Version**: 1.0
**Status**: Production Ready
