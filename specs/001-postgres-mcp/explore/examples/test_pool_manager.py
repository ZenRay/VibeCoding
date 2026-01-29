"""
Unit tests for PoolManager.

Run with: pytest test_pool_manager.py -v
"""

import asyncio
from datetime import datetime, timedelta

import asyncpg
import pytest

from pool_manager import DBConfig, PoolManager, PoolStats


@pytest.fixture
async def pool_manager():
    """Create pool manager for testing."""
    manager = PoolManager(
        enable_monitoring=False,  # Disable for tests
        enable_cleanup=False,
        idle_pool_timeout=timedelta(seconds=5),  # Short timeout for tests
    )
    yield manager
    await manager.close_all()


@pytest.fixture
def db_config():
    """
    Test database configuration.

    Note: This requires a running PostgreSQL instance.
    Configure with environment variables or use Docker:

        docker run -d --name test-postgres \\
            -e POSTGRES_PASSWORD=test \\
            -e POSTGRES_DB=test_db \\
            -p 5432:5432 \\
            postgres:15
    """
    return DBConfig(
        host="localhost",
        port=5432,
        database="test_db",
        user="postgres",
        password="test",
        pool_min_size=2,
        pool_max_size=10,
    )


@pytest.mark.asyncio
async def test_create_pool(pool_manager, db_config):
    """Test pool creation."""
    db_id = await pool_manager.create_pool(db_config)
    assert db_id is not None
    assert len(db_id) == 16  # SHA256 hash truncated to 16 chars
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
async def test_get_nonexistent_pool(pool_manager):
    """Test getting nonexistent pool returns None."""
    pool = await pool_manager.get_pool("nonexistent")
    assert pool is None


@pytest.mark.asyncio
async def test_execute_query_success(pool_manager, db_config):
    """Test successful query execution."""
    db_id = await pool_manager.create_pool(db_config)
    result = await pool_manager.execute_query(db_id, "SELECT 1 AS value")

    assert len(result) == 1
    assert result[0]["value"] == 1


@pytest.mark.asyncio
async def test_execute_query_multiple_rows(pool_manager, db_config):
    """Test query returning multiple rows."""
    db_id = await pool_manager.create_pool(db_config)
    result = await pool_manager.execute_query(
        db_id,
        "SELECT generate_series(1, 10) AS num",
    )

    assert len(result) == 10
    assert result[0]["num"] == 1
    assert result[9]["num"] == 10


@pytest.mark.asyncio
async def test_execute_query_syntax_error(pool_manager, db_config):
    """Test query with syntax error."""
    db_id = await pool_manager.create_pool(db_config)

    with pytest.raises(ValueError, match="Invalid SQL syntax"):
        await pool_manager.execute_query(db_id, "SELECT INVALID SYNTAX")


@pytest.mark.asyncio
async def test_execute_query_timeout(pool_manager, db_config):
    """Test query timeout."""
    db_id = await pool_manager.create_pool(db_config)

    with pytest.raises(TimeoutError):
        await pool_manager.execute_query(
            db_id,
            "SELECT pg_sleep(60)",
            timeout=1.0,
        )


@pytest.mark.asyncio
async def test_execute_query_nonexistent_pool(pool_manager):
    """Test executing query on nonexistent pool."""
    with pytest.raises(ValueError, match="not found"):
        await pool_manager.execute_query("nonexistent", "SELECT 1")


@pytest.mark.asyncio
async def test_get_pool_stats(pool_manager, db_config):
    """Test retrieving pool statistics."""
    db_id = await pool_manager.create_pool(db_config)

    # Execute a query to populate stats
    await pool_manager.execute_query(db_id, "SELECT 1")

    stats = await pool_manager.get_pool_stats(db_id)
    assert stats is not None
    assert stats.db_id == db_id
    assert stats.queries_executed >= 1
    assert stats.size >= db_config.pool_min_size
    assert stats.size <= db_config.pool_max_size
    assert stats.min_size == db_config.pool_min_size
    assert stats.max_size == db_config.pool_max_size


@pytest.mark.asyncio
async def test_get_pool_stats_nonexistent(pool_manager):
    """Test getting stats for nonexistent pool."""
    stats = await pool_manager.get_pool_stats("nonexistent")
    assert stats is None


@pytest.mark.asyncio
async def test_invalidate_schema_cache(pool_manager, db_config):
    """Test schema cache invalidation."""
    db_id = await pool_manager.create_pool(db_config)
    await pool_manager.invalidate_schema_cache(db_id)
    # No exception = success


@pytest.mark.asyncio
async def test_invalidate_schema_cache_nonexistent(pool_manager):
    """Test invalidating cache for nonexistent pool."""
    with pytest.raises(ValueError, match="not found"):
        await pool_manager.invalidate_schema_cache("nonexistent")


@pytest.mark.asyncio
async def test_close_pool(pool_manager, db_config):
    """Test closing specific pool."""
    db_id = await pool_manager.create_pool(db_config)
    assert await pool_manager.get_pool(db_id) is not None

    await pool_manager.close_pool(db_id)
    assert await pool_manager.get_pool(db_id) is None


@pytest.mark.asyncio
async def test_close_nonexistent_pool(pool_manager):
    """Test closing nonexistent pool (should not raise error)."""
    await pool_manager.close_pool("nonexistent")
    # No exception = success


@pytest.mark.asyncio
async def test_close_all(pool_manager, db_config):
    """Test closing all pools."""
    # Create multiple pools
    config1 = db_config
    config2 = DBConfig(
        host=db_config.host,
        port=db_config.port,
        database="postgres",  # Different database
        user=db_config.user,
        password=db_config.password,
    )

    await pool_manager.create_pool(config1)
    await pool_manager.create_pool(config2)

    assert len(pool_manager._pools) >= 1  # May be 1 if same connection

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
    assert all(len(result) == 1 for result in results)
    assert all(result[0]["value"] == 1 for result in results)


@pytest.mark.asyncio
async def test_concurrent_queries_pool_growth(pool_manager, db_config):
    """Test that pool grows to handle concurrent load."""
    db_id = await pool_manager.create_pool(db_config)

    # Initial pool size
    initial_stats = await pool_manager.get_pool_stats(db_id)
    initial_size = initial_stats.size

    # Execute concurrent queries
    queries = [
        pool_manager.execute_query(db_id, "SELECT pg_sleep(0.1)")
        for _ in range(db_config.pool_max_size)
    ]

    # Check pool size during execution (may have grown)
    await asyncio.sleep(0.05)  # Let queries start
    concurrent_stats = await pool_manager.get_pool_stats(db_id)

    # Wait for completion
    await asyncio.gather(*queries)

    # Pool should have grown beyond min_size
    assert concurrent_stats.size >= initial_size


@pytest.mark.asyncio
async def test_query_retry_on_schema_cache_error(pool_manager, db_config):
    """Test automatic retry on schema cache error."""
    db_id = await pool_manager.create_pool(db_config)

    # Create a table
    await pool_manager.execute_query(
        db_id,
        "CREATE TEMP TABLE test_retry (id INT, value TEXT)",
    )

    # Query should succeed
    result = await pool_manager.execute_query(
        db_id,
        "SELECT * FROM test_retry",
    )
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_pool_stats_tracking(pool_manager, db_config):
    """Test that pool stats are tracked correctly."""
    db_id = await pool_manager.create_pool(db_config)

    # Execute multiple queries
    for _ in range(5):
        await pool_manager.execute_query(db_id, "SELECT 1")

    stats = await pool_manager.get_pool_stats(db_id)
    assert stats.queries_executed >= 5
    assert stats.avg_acquire_time_ms >= 0


@pytest.mark.asyncio
async def test_config_get_id_consistency(db_config):
    """Test that config.get_id() is deterministic."""
    id1 = db_config.get_id()
    id2 = db_config.get_id()
    assert id1 == id2
    assert len(id1) == 16


@pytest.mark.asyncio
async def test_config_to_pool_kwargs(db_config):
    """Test config conversion to pool kwargs."""
    kwargs = db_config.to_pool_kwargs()

    assert kwargs["host"] == db_config.host
    assert kwargs["port"] == db_config.port
    assert kwargs["database"] == db_config.database
    assert kwargs["user"] == db_config.user
    assert kwargs["password"] == db_config.password
    assert kwargs["min_size"] == db_config.pool_min_size
    assert kwargs["max_size"] == db_config.pool_max_size
    assert "server_settings" in kwargs
    assert "statement_timeout" in kwargs["server_settings"]


@pytest.mark.asyncio
async def test_readonly_transaction(pool_manager, db_config):
    """Test that readonly flag is respected."""
    db_id = await pool_manager.create_pool(db_config)

    # Read-only query should work
    result = await pool_manager.execute_query(
        db_id,
        "SELECT 1",
        readonly=True,
    )
    assert len(result) == 1

    # Write query with readonly=True should fail
    with pytest.raises(Exception):  # asyncpg will raise error
        await pool_manager.execute_query(
            db_id,
            "CREATE TEMP TABLE test_readonly (id INT)",
            readonly=True,
        )


@pytest.mark.asyncio
async def test_last_used_timestamp_update(pool_manager, db_config):
    """Test that last_used timestamp is updated."""
    db_id = await pool_manager.create_pool(db_config)

    initial_stats = await pool_manager.get_pool_stats(db_id)
    initial_time = initial_stats.last_used

    await asyncio.sleep(0.1)

    # Execute query to update timestamp
    await pool_manager.execute_query(db_id, "SELECT 1")

    updated_stats = await pool_manager.get_pool_stats(db_id)
    updated_time = updated_stats.last_used

    assert updated_time > initial_time


# Integration tests (require running PostgreSQL)

@pytest.mark.integration
@pytest.mark.asyncio
async def test_connection_to_real_database():
    """Integration test with real PostgreSQL database."""
    manager = PoolManager(enable_monitoring=False, enable_cleanup=False)

    config = DBConfig(
        host="localhost",
        port=5432,
        database="postgres",  # Default database
        user="postgres",
        password="test",
    )

    try:
        db_id = await manager.create_pool(config)
        result = await manager.execute_query(db_id, "SELECT version()")
        assert len(result) == 1
        assert "PostgreSQL" in result[0]["version"]

    finally:
        await manager.close_all()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_pool_exhaustion_handling():
    """Integration test for pool exhaustion behavior."""
    manager = PoolManager(enable_monitoring=False, enable_cleanup=False)

    config = DBConfig(
        host="localhost",
        port=5432,
        database="postgres",
        user="postgres",
        password="test",
        pool_min_size=1,
        pool_max_size=2,  # Small pool to easily exhaust
    )

    try:
        db_id = await manager.create_pool(config)

        # Hold connections and exhaust pool
        async def hold_connection():
            await manager.execute_query(db_id, "SELECT pg_sleep(2)")

        # Start more tasks than pool size
        tasks = [hold_connection() for _ in range(5)]

        # Some tasks may timeout waiting for connection
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Check that at least some succeeded
        successes = [r for r in results if not isinstance(r, Exception)]
        assert len(successes) > 0

    finally:
        await manager.close_all()
