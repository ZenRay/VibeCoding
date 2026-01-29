"""
FastMCP server implementation.

Main entry point for the PostgreSQL MCP server with lifespan management.
"""

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server

from postgres_mcp.ai.openai_client import OpenAIClient
from postgres_mcp.config import Config
from postgres_mcp.core.query_executor import QueryExecutor
from postgres_mcp.core.schema_cache import SchemaCache
from postgres_mcp.core.sql_generator import SQLGenerator
from postgres_mcp.core.sql_validator import SQLValidator
from postgres_mcp.db.connection_pool import PoolManager
from postgres_mcp.db.query_runner import QueryRunner
from postgres_mcp.db.schema_inspector import SchemaInspector
from postgres_mcp.mcp.resources import register_resources
from postgres_mcp.mcp.tools import register_tools
from postgres_mcp.utils.jsonl_writer import JSONLWriter

logger = structlog.get_logger(__name__)


class ServerContext:
    """
    Shared server context for MCP tools and resources.

    Holds all service instances needed for MCP operations.
    """

    def __init__(self):
        """Initialize empty context."""
        self.schema_cache: SchemaCache | None = None
        self.sql_generator: SQLGenerator | None = None
        self.sql_validator: SQLValidator | None = None
        self.openai_client: OpenAIClient | None = None
        self.pool_manager: PoolManager | None = None
        self.query_runner: QueryRunner | None = None
        self.query_executor: QueryExecutor | None = None
        self.jsonl_writer: JSONLWriter | None = None


# Global server context
_context = ServerContext()


def get_context() -> ServerContext:
    """
    Get global server context.

    Returns:
    ----------
        ServerContext instance

    Example:
    ----------
        >>> ctx = get_context()
        >>> schema = await ctx.schema_cache.get_schema("mydb")
    """
    return _context


@asynccontextmanager
async def server_lifespan():
    """
    Server lifespan context manager.

    Handles initialization and cleanup of all server resources.

    Yields:
    ----------
        None

    Example:
    ----------
        >>> async with server_lifespan():
        ...     # Server is running
        ...     pass
    """
    logger.info("postgres_mcp_server_starting")

    try:
        # Load configuration
        config = Config.load()
        logger.info(
            "config_loaded",
            database_count=len(config.databases),
            openai_model=config.openai.model,
        )

        # Initialize OpenAI client
        _context.openai_client = OpenAIClient(
            api_key=config.openai.resolved_api_key,
            model=config.openai.model,
            temperature=config.openai.temperature,
            max_tokens=config.openai.max_tokens,
            timeout=config.openai.timeout,
            base_url=config.openai.base_url,
        )
        logger.info("openai_client_initialized")

        # Initialize SQL validator
        _context.sql_validator = SQLValidator()
        logger.info("sql_validator_initialized")

        # Initialize connection pool manager
        _context.pool_manager = PoolManager(db_configs=config.databases)
        await _context.pool_manager.initialize()
        logger.info("pool_manager_initialized")

        # Initialize query runner
        _context.query_runner = QueryRunner(timeout_seconds=30.0)
        logger.info("query_runner_initialized")

        # Initialize JSONL writer for query history
        log_dir = Path(config.logging.directory)
        _context.jsonl_writer = JSONLWriter(
            log_directory=log_dir,
            buffer_size=config.logging.buffer_size,
            flush_interval_seconds=config.logging.flush_interval_seconds,
            max_file_size_mb=config.logging.max_file_size_mb,
            retention_days=config.logging.retention_days,
        )
        await _context.jsonl_writer.start()
        logger.info("jsonl_writer_initialized", log_directory=str(log_dir))

        # Initialize schema inspectors for each database
        inspectors = {}
        for db_config in config.databases:
            inspector = SchemaInspector(
                host=db_config.host,
                port=db_config.port,
                user=db_config.user,
                password=db_config.password,
                database=db_config.database,
            )
            inspectors[db_config.name] = inspector

        # Initialize schema cache
        _context.schema_cache = SchemaCache(
            databases=inspectors,
            auto_refresh_interval=300,  # 5 minutes
        )
        await _context.schema_cache.initialize()
        logger.info("schema_cache_initialized")

        # Initialize SQL generator
        _context.sql_generator = SQLGenerator(
            schema_cache=_context.schema_cache,
            openai_client=_context.openai_client,
            sql_validator=_context.sql_validator,
        )
        logger.info("sql_generator_initialized")

        # Initialize query executor
        _context.query_executor = QueryExecutor(
            sql_generator=_context.sql_generator,
            pool_manager=_context.pool_manager,
            query_runner=_context.query_runner,
            jsonl_writer=_context.jsonl_writer,
        )
        logger.info("query_executor_initialized")

        logger.info("postgres_mcp_server_ready")

        # Server is now running
        yield

    except Exception as e:
        logger.error("server_initialization_failed", error=str(e))
        raise

    finally:
        # Comprehensive cleanup with error handling
        # Note: Only log if stdout is still available (not during forced termination)

        cleanup_errors = []

        # Stop JSONL writer and flush remaining buffer
        if _context.jsonl_writer:
            try:
                await _context.jsonl_writer.stop()
            except Exception as e:
                cleanup_errors.append(f"jsonl_writer: {str(e)}")

        # Close connection pool manager
        if _context.pool_manager:
            try:
                await _context.pool_manager.close_all()
            except Exception as e:
                cleanup_errors.append(f"pool_manager: {str(e)}")

        # Cleanup schema cache
        if _context.schema_cache:
            try:
                await _context.schema_cache.cleanup()
            except Exception as e:
                cleanup_errors.append(f"schema_cache: {str(e)}")

        # Try to log cleanup status if possible
        try:
            if cleanup_errors:
                logger.warning(
                    "cleanup_completed_with_errors",
                    error_count=len(cleanup_errors),
                    errors=cleanup_errors,
                )
            else:
                logger.info("postgres_mcp_server_stopped_cleanly")
        except (ValueError, OSError):
            # stdout/stderr closed - silently exit
            pass


async def main():
    """
    Main entry point for the MCP server with comprehensive error handling.

    Starts the server with stdio transport and registers all tools and resources.
    Handles all errors gracefully to prevent unexpected crashes.
    """
    try:
        # Create MCP server
        server = Server("postgres-mcp")

        # Register tools and resources
        register_tools(server)
        register_resources(server)

        logger.info("mcp_tools_and_resources_registered")

        # Run server with lifespan management
        async with server_lifespan():
            async with stdio_server() as (read_stream, write_stream):
                logger.info("mcp_server_started_stdio")
                await server.run(
                    read_stream,
                    write_stream,
                    server.create_initialization_options(),
                )
    except KeyboardInterrupt:
        # Silently handle Ctrl+C
        pass
    except Exception as e:
        try:
            logger.error(
                "server_main_failed",
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True,
            )
        except (ValueError, OSError):
            # stdout closed - silently exit
            pass
        raise


def run():
    """
    Synchronous entry point for the server with comprehensive error handling.

    Used by __main__.py and CLI commands.
    Ensures all errors are logged and handled gracefully.
    """
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Silently handle Ctrl+C
        pass
    except Exception as e:
        try:
            logger.error(
                "server_failed",
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True,
            )
        except (ValueError, OSError):
            # stdout closed - silently exit
            pass
        raise


if __name__ == "__main__":
    run()
