"""
Unit tests for JSONLWriter (query history logging).

Tests cover:
- Async buffered writes
- Automatic flushing (5 second interval)
- Log rotation (file size limits)
- Log cleanup (30 day retention)
- Graceful shutdown and cleanup
- Error handling
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from postgres_mcp.models.log_entry import LogStatus, QueryLogEntry
from postgres_mcp.utils.jsonl_writer import JSONLWriter


@pytest.fixture
def log_dir(tmp_path: Path) -> Path:
    """Create a temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir


@pytest.fixture
def log_entry() -> QueryLogEntry:
    """Create a sample log entry."""
    return QueryLogEntry(
        request_id="test-123",
        database="test_db",
        natural_language="show all users",
        sql="SELECT * FROM users",
        status=LogStatus.SUCCESS,
        execution_time_ms=15.5,
        row_count=42,
    )


@pytest.mark.asyncio
class TestJSONLWriter:
    """Test JSONLWriter functionality."""

    async def test_initialization(self, log_dir: Path) -> None:
        """Test JSONLWriter initialization."""
        writer = JSONLWriter(
            log_directory=log_dir,
            buffer_size=100,
            flush_interval_seconds=5.0,
        )

        assert writer.log_directory == log_dir
        assert writer.buffer_size == 100
        assert writer.flush_interval_seconds == 5.0
        assert len(writer._buffer) == 0
        assert not writer._is_running

    async def test_write_single_entry(self, log_dir: Path, log_entry: QueryLogEntry) -> None:
        """Test writing a single log entry."""
        writer = JSONLWriter(log_directory=log_dir, buffer_size=10)

        await writer.start()
        await writer.write(log_entry)
        await writer.stop()

        # Verify log file exists and contains entry
        log_files = list(log_dir.glob("query_history_*.jsonl"))
        assert len(log_files) == 1

        content = log_files[0].read_text()
        assert "test-123" in content
        assert "show all users" in content
        assert "SELECT * FROM users" in content

    async def test_buffered_writes(self, log_dir: Path, log_entry: QueryLogEntry) -> None:
        """Test buffered writes (multiple entries before flush)."""
        writer = JSONLWriter(log_directory=log_dir, buffer_size=5)

        await writer.start()

        # Write 3 entries (below buffer size)
        for i in range(3):
            entry = QueryLogEntry(
                request_id=f"test-{i}",
                database="test_db",
                natural_language=f"query {i}",
                sql=f"SELECT {i}",
                status=LogStatus.SUCCESS,
            )
            await writer.write(entry)

        # Buffer should have 3 entries
        assert len(writer._buffer) == 3

        # Manually flush
        await writer.flush()

        # Buffer should be empty
        assert len(writer._buffer) == 0

        # Verify log file contains all entries
        log_files = list(log_dir.glob("query_history_*.jsonl"))
        assert len(log_files) == 1

        content = log_files[0].read_text()
        for i in range(3):
            assert f"test-{i}" in content
            assert f"query {i}" in content

    async def test_buffer_auto_flush_on_full(self, log_dir: Path, log_entry: QueryLogEntry) -> None:
        """Test automatic flush when buffer is full."""
        writer = JSONLWriter(log_directory=log_dir, buffer_size=5)

        await writer.start()

        # Write exactly buffer_size entries
        for i in range(5):
            entry = QueryLogEntry(
                request_id=f"test-{i}",
                database="test_db",
                natural_language=f"query {i}",
                sql=f"SELECT {i}",
                status=LogStatus.SUCCESS,
            )
            await writer.write(entry)

        # Buffer should auto-flush and be empty
        await asyncio.sleep(0.1)  # Allow flush to complete
        assert len(writer._buffer) == 0

        await writer.stop()

        # Verify all entries were written
        log_files = list(log_dir.glob("query_history_*.jsonl"))
        content = log_files[0].read_text()
        lines = [line for line in content.strip().split("\n") if line]
        assert len(lines) == 5

    async def test_periodic_flush(self, log_dir: Path, log_entry: QueryLogEntry) -> None:
        """Test periodic flush (every 5 seconds)."""
        writer = JSONLWriter(log_directory=log_dir, buffer_size=100, flush_interval_seconds=1.0)

        await writer.start()

        # Write 2 entries
        for i in range(2):
            entry = QueryLogEntry(
                request_id=f"test-{i}",
                database="test_db",
                natural_language=f"query {i}",
                sql=f"SELECT {i}",
                status=LogStatus.SUCCESS,
            )
            await writer.write(entry)

        # Buffer should have 2 entries
        assert len(writer._buffer) == 2

        # Wait for periodic flush (1 second + margin)
        await asyncio.sleep(1.5)

        # Buffer should be empty after flush
        assert len(writer._buffer) == 0

        await writer.stop()

        # Verify entries were written
        log_files = list(log_dir.glob("query_history_*.jsonl"))
        content = log_files[0].read_text()
        lines = [line for line in content.strip().split("\n") if line]
        assert len(lines) == 2

    async def test_log_rotation(self, log_dir: Path, log_entry: QueryLogEntry) -> None:
        """Test log rotation when file size exceeds limit."""
        # Set very small max file size to trigger rotation
        writer = JSONLWriter(
            log_directory=log_dir,
            buffer_size=1,
            max_file_size_mb=0.001,  # 1KB
        )

        await writer.start()

        # Write many entries to exceed file size limit
        for i in range(50):
            entry = QueryLogEntry(
                request_id=f"test-{i}" * 10,  # Make entries larger
                database="test_db",
                natural_language=f"query {i}" * 20,
                sql=f"SELECT {i}" * 20,
                status=LogStatus.SUCCESS,
            )
            await writer.write(entry)

        await writer.stop()

        # Should have created multiple log files due to rotation
        log_files = list(log_dir.glob("query_history_*.jsonl"))
        assert len(log_files) >= 2

    async def test_log_cleanup(self, log_dir: Path) -> None:
        """Test cleanup of old log files (30 day retention)."""
        writer = JSONLWriter(log_directory=log_dir, retention_days=7)

        # Create old log file (8 days old)
        old_date = datetime.now(UTC) - timedelta(days=8)
        old_file = log_dir / f"query_history_{old_date.strftime('%Y%m%d')}_000001.jsonl"
        old_file.write_text('{"test": "old"}\n')

        # Create recent log file (3 days old)
        recent_date = datetime.now(UTC) - timedelta(days=3)
        recent_file = log_dir / f"query_history_{recent_date.strftime('%Y%m%d')}_000001.jsonl"
        recent_file.write_text('{"test": "recent"}\n')

        # Run cleanup
        await writer._cleanup_old_logs()

        # Old file should be deleted, recent file should remain
        assert not old_file.exists()
        assert recent_file.exists()

    async def test_graceful_shutdown(self, log_dir: Path, log_entry: QueryLogEntry) -> None:
        """Test graceful shutdown flushes pending entries."""
        writer = JSONLWriter(log_directory=log_dir, buffer_size=100)

        await writer.start()

        # Write entries without waiting for flush
        for i in range(3):
            entry = QueryLogEntry(
                request_id=f"test-{i}",
                database="test_db",
                natural_language=f"query {i}",
                sql=f"SELECT {i}",
                status=LogStatus.SUCCESS,
            )
            await writer.write(entry)

        # Buffer should have 3 entries
        assert len(writer._buffer) == 3

        # Stop should flush remaining buffer
        await writer.stop()

        # Buffer should be empty
        assert len(writer._buffer) == 0

        # Verify all entries were written
        log_files = list(log_dir.glob("query_history_*.jsonl"))
        content = log_files[0].read_text()
        lines = [line for line in content.strip().split("\n") if line]
        assert len(lines) == 3

    async def test_error_handling_write_failure(
        self, log_dir: Path, log_entry: QueryLogEntry
    ) -> None:
        """Test error handling when file write fails."""
        writer = JSONLWriter(log_directory=log_dir, buffer_size=1)

        await writer.start()

        # Mock file write to raise error
        with patch("pathlib.Path.open", side_effect=OSError("Disk full")):
            # Write should not crash even if flush fails
            await writer.write(log_entry)
            await asyncio.sleep(0.2)  # Wait for flush attempt

        # Writer should still be running
        assert writer._is_running

        await writer.stop()

    async def test_concurrent_writes(self, log_dir: Path, log_entry: QueryLogEntry) -> None:
        """Test thread-safe concurrent writes."""
        writer = JSONLWriter(log_directory=log_dir, buffer_size=100)

        await writer.start()

        # Concurrent writes from multiple tasks
        async def write_entries(start: int, count: int) -> None:
            for i in range(start, start + count):
                entry = QueryLogEntry(
                    request_id=f"test-{i}",
                    database="test_db",
                    natural_language=f"query {i}",
                    sql=f"SELECT {i}",
                    status=LogStatus.SUCCESS,
                )
                await writer.write(entry)

        # Launch 3 concurrent writers
        await asyncio.gather(write_entries(0, 10), write_entries(10, 10), write_entries(20, 10))

        await writer.stop()

        # Verify all 30 entries were written
        log_files = list(log_dir.glob("query_history_*.jsonl"))
        content = log_files[0].read_text()
        lines = [line for line in content.strip().split("\n") if line]
        assert len(lines) == 30

    async def test_context_manager(self, log_dir: Path, log_entry: QueryLogEntry) -> None:
        """Test using JSONLWriter as async context manager."""
        async with JSONLWriter(log_directory=log_dir, buffer_size=10) as writer:
            await writer.write(log_entry)
            assert writer._is_running

        # Should auto-stop and flush on context exit
        assert not writer._is_running

        # Verify entry was written
        log_files = list(log_dir.glob("query_history_*.jsonl"))
        assert len(log_files) == 1
        content = log_files[0].read_text()
        assert "test-123" in content
