"""
JSONL writer for query history logging.

This module provides an async, buffered JSONL writer for logging query
execution history. It supports:
- Async buffered writes with automatic flushing
- Periodic flush (default 5 seconds)
- Log rotation based on file size
- Automatic cleanup of old log files (default 30 days retention)
- Thread-safe concurrent writes
- Graceful shutdown

Args:
----------
    None

Returns:
----------
    None

Raises:
----------
    None
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from postgres_mcp.models.log_entry import QueryLogEntry

logger = structlog.get_logger(__name__)


class JSONLWriter:
    """
    Async JSONL writer for query history logging.

    Provides buffered, thread-safe writing of query log entries to JSONL files
    with automatic rotation and cleanup.

    Args:
    ----------
        log_directory: Directory path for log files
        buffer_size: Number of entries to buffer before flushing (default 100)
        flush_interval_seconds: Automatic flush interval in seconds (default 5.0)
        max_file_size_mb: Maximum log file size before rotation in MB (default 100)
        retention_days: Days to retain log files (default 30)

    Returns:
    ----------
        None

    Raises:
    ----------
        None

    Example:
    ----------
        >>> writer = JSONLWriter(log_directory=Path("logs"))
        >>> await writer.start()
        >>> await writer.write(log_entry)
        >>> await writer.stop()
    """

    def __init__(
        self,
        log_directory: Path | str,
        buffer_size: int = 100,
        flush_interval_seconds: float = 5.0,
        max_file_size_mb: int = 100,
        retention_days: int = 30,
    ) -> None:
        """
        Initialize JSONLWriter.

        Args:
        ----------
            log_directory: Directory path for log files
            buffer_size: Number of entries to buffer before flushing
            flush_interval_seconds: Automatic flush interval in seconds
            max_file_size_mb: Maximum log file size before rotation in MB
            retention_days: Days to retain log files

        Returns:
        ----------
            None

        Raises:
        ----------
            None
        """
        self.log_directory = Path(log_directory)
        self.buffer_size = buffer_size
        self.flush_interval_seconds = flush_interval_seconds
        self.max_file_size_mb = max_file_size_mb
        self.retention_days = retention_days

        # Internal state
        self._buffer: list[QueryLogEntry] = []
        self._lock = asyncio.Lock()
        self._is_running = False
        self._flush_task: asyncio.Task[None] | None = None
        self._current_file: Path | None = None
        self._current_file_sequence = 1

        # Ensure log directory exists
        self.log_directory.mkdir(parents=True, exist_ok=True)

        logger.info(
            "jsonl_writer_initialized",
            log_directory=str(self.log_directory),
            buffer_size=buffer_size,
            flush_interval_seconds=flush_interval_seconds,
        )

    async def start(self) -> None:
        """
        Start the JSONL writer and background flush task.

        Args:
        ----------
            None

        Returns:
        ----------
            None

        Raises:
        ----------
            None
        """
        if self._is_running:
            logger.warning("jsonl_writer_already_running")
            return

        self._is_running = True
        self._flush_task = asyncio.create_task(self._periodic_flush())

        # Run initial cleanup
        await self._cleanup_old_logs()

        logger.info("jsonl_writer_started")

    async def stop(self) -> None:
        """
        Stop the JSONL writer and flush remaining buffer.

        Args:
        ----------
            None

        Returns:
        ----------
            None

        Raises:
        ----------
            None
        """
        if not self._is_running:
            return

        self._is_running = False

        # Cancel flush task
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass

        # Flush remaining buffer
        await self.flush()

        logger.info("jsonl_writer_stopped", entries_flushed=len(self._buffer))

    async def write(self, entry: QueryLogEntry) -> None:
        """
        Write a log entry to the buffer (async, non-blocking).

        Args:
        ----------
            entry: Query log entry to write

        Returns:
        ----------
            None

        Raises:
        ----------
            None
        """
        async with self._lock:
            self._buffer.append(entry)

            # Auto-flush if buffer is full
            if len(self._buffer) >= self.buffer_size:
                await self._flush_buffer()

    async def flush(self) -> None:
        """
        Manually flush the buffer to disk.

        Args:
        ----------
            None

        Returns:
        ----------
            None

        Raises:
        ----------
            None
        """
        async with self._lock:
            await self._flush_buffer()

    async def _flush_buffer(self) -> None:
        """
        Flush buffer to disk (internal, must hold lock).

        Args:
        ----------
            None

        Returns:
        ----------
            None

        Raises:
        ----------
            None
        """
        if not self._buffer:
            return

        try:
            # Get or create log file
            log_file = self._get_current_log_file()

            # Write entries to file
            with log_file.open("a", encoding="utf-8") as f:
                for entry in self._buffer:
                    f.write(entry.to_jsonl() + "\n")

            logger.debug(
                "buffer_flushed",
                entries_count=len(self._buffer),
                log_file=str(log_file),
            )

            # Clear buffer
            self._buffer.clear()

            # Check if rotation is needed
            await self._check_rotation(log_file)

        except Exception as e:
            logger.error(
                "buffer_flush_failed",
                error=str(e),
                error_type=type(e).__name__,
                entries_count=len(self._buffer),
            )
            # Don't clear buffer on failure - will retry on next flush

    def _get_current_log_file(self) -> Path:
        """
        Get the current log file path, creating a new one if needed.

        Args:
        ----------
            None

        Returns:
        ----------
            Path to current log file

        Raises:
        ----------
            None
        """
        if self._current_file and self._current_file.exists():
            return self._current_file

        # Generate new log file name
        date_str = datetime.now(UTC).strftime("%Y%m%d")
        filename = f"query_history_{date_str}_{self._current_file_sequence:06d}.jsonl"
        self._current_file = self.log_directory / filename

        logger.info("new_log_file_created", log_file=str(self._current_file))

        return self._current_file

    async def _check_rotation(self, log_file: Path) -> None:
        """
        Check if log rotation is needed based on file size.

        Args:
        ----------
            log_file: Path to current log file

        Returns:
        ----------
            None

        Raises:
        ----------
            None
        """
        try:
            file_size_mb = log_file.stat().st_size / (1024 * 1024)

            if file_size_mb >= self.max_file_size_mb:
                logger.info(
                    "log_rotation_triggered",
                    log_file=str(log_file),
                    file_size_mb=round(file_size_mb, 2),
                )

                # Increment sequence for next file
                self._current_file_sequence += 1
                self._current_file = None

        except Exception as e:
            logger.error("rotation_check_failed", error=str(e), error_type=type(e).__name__)

    async def _periodic_flush(self) -> None:
        """
        Background task for periodic buffer flushing.

        Args:
        ----------
            None

        Returns:
        ----------
            None

        Raises:
        ----------
            None
        """
        while self._is_running:
            try:
                await asyncio.sleep(self.flush_interval_seconds)

                async with self._lock:
                    if self._buffer:
                        await self._flush_buffer()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("periodic_flush_failed", error=str(e), error_type=type(e).__name__)

    async def _cleanup_old_logs(self) -> None:
        """
        Clean up log files older than retention period.

        Args:
        ----------
            None

        Returns:
        ----------
            None

        Raises:
        ----------
            None
        """
        try:
            cutoff_date = datetime.now(UTC) - timedelta(days=self.retention_days)
            deleted_count = 0

            for log_file in self.log_directory.glob("query_history_*.jsonl"):
                try:
                    # Parse date from filename (query_history_YYYYMMDD_NNNNNN.jsonl)
                    date_str = log_file.stem.split("_")[2]
                    file_date = datetime.strptime(date_str, "%Y%m%d").replace(tzinfo=UTC)

                    if file_date < cutoff_date:
                        log_file.unlink()
                        deleted_count += 1
                        logger.debug("old_log_deleted", log_file=str(log_file))

                except (IndexError, ValueError) as e:
                    logger.warning(
                        "log_cleanup_parse_error",
                        log_file=str(log_file),
                        error=str(e),
                    )
                    continue

            if deleted_count > 0:
                logger.info(
                    "log_cleanup_completed",
                    deleted_count=deleted_count,
                    retention_days=self.retention_days,
                )

        except Exception as e:
            logger.error("log_cleanup_failed", error=str(e), error_type=type(e).__name__)

    async def __aenter__(self) -> JSONLWriter:
        """
        Async context manager entry.

        Args:
        ----------
            None

        Returns:
        ----------
            The JSONLWriter instance

        Raises:
        ----------
            None
        """
        await self.start()
        return self

    async def __aexit__(self, exc_type: type, exc_val: Exception, exc_tb: object) -> None:
        """
        Async context manager exit.

        Args:
        ----------
            exc_type: Exception type if raised
            exc_val: Exception value if raised
            exc_tb: Exception traceback if raised

        Returns:
        ----------
            None

        Raises:
        ----------
            None
        """
        await self.stop()
