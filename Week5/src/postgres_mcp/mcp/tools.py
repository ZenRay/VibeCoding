"""
MCP tools implementation.

Implements all MCP tools for PostgreSQL operations with robust error handling.
"""

import asyncio
from typing import Any

import structlog
from mcp.server import Server
from mcp.types import TextContent, Tool

logger = structlog.get_logger(__name__)


def register_tools(server: Server) -> None:
    """
    Register all MCP tools with the server.

    Args:
    ----------
        server: MCP Server instance
    """

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """
        List all available tools.

        Returns:
        ----------
            List of tool definitions
        """
        return [
            Tool(
                name="generate_sql",
                description=(
                    "Generate PostgreSQL SELECT query from natural language. "
                    "Automatically validates query for security (read-only). "
                    "Returns validated SQL with warnings if any."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "natural_language": {
                            "type": "string",
                            "description": "Natural language description of the query",
                        },
                        "database": {
                            "type": "string",
                            "description": (
                                "Target database name "
                                "(optional, uses default if not specified)"
                            ),
                        },
                    },
                    "required": ["natural_language"],
                },
            ),
            Tool(
                name="execute_query",
                description=(
                    "Generate and execute PostgreSQL query from natural language. "
                    "Returns SQL along with actual query results (columns and rows). "
                    "Automatically enforces read-only access and row limits."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "natural_language": {
                            "type": "string",
                            "description": "Natural language description of the query",
                        },
                        "database": {
                            "type": "string",
                            "description": (
                                "Target database name "
                                "(optional, uses default if not specified)"
                            ),
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum rows to return (default: 1000, max: 10000)",
                            "minimum": 1,
                            "maximum": 10000,
                        },
                    },
                    "required": ["natural_language"],
                },
            ),
            Tool(
                name="list_databases",
                description="List all configured databases with their schema information.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            Tool(
                name="refresh_schema",
                description=(
                    "Manually refresh schema cache for a specific database or all databases. "
                    "Useful after schema changes (ALTER TABLE, etc.)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "database": {
                            "type": "string",
                            "description": "Database name (omit to refresh all databases)",
                        },
                    },
                },
            ),
            Tool(
                name="query_history",
                description=(
                    "Retrieve query execution history from logs. "
                    "Filter by database, status, or time range. "
                    "Returns recent query logs with execution details."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "database": {
                            "type": "string",
                            "description": "Filter by database name (optional)",
                        },
                        "status": {
                            "type": "string",
                            "enum": [
                                "success",
                                "validation_failed",
                                "execution_failed",
                                "ai_failed",
                            ],
                            "description": "Filter by execution status (optional)",
                        },
                        "limit": {
                            "type": "integer",
                            "description": (
                                "Maximum number of entries to return " "(default: 50, max: 500)"
                            ),
                            "minimum": 1,
                            "maximum": 500,
                        },
                    },
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """
        Handle tool calls with comprehensive error handling.

        Args:
        ----------
            name: Tool name
            arguments: Tool arguments

        Returns:
        ----------
            List of text content responses

        Note:
        ----------
            All exceptions are caught and converted to user-friendly error messages
            to prevent server crashes.
        """
        from postgres_mcp.server import get_context

        ctx = get_context()

        logger.info("tool_call_started", tool=name, args=arguments)

        try:
            if name == "generate_sql":
                result = await handle_generate_sql(arguments, ctx)
            elif name == "execute_query":
                result = await handle_execute_query(arguments, ctx)
            elif name == "list_databases":
                result = await handle_list_databases(ctx)
            elif name == "refresh_schema":
                result = await handle_refresh_schema(arguments, ctx)
            elif name == "query_history":
                result = await handle_query_history(arguments, ctx)
            else:
                logger.warning("unknown_tool_called", tool=name)
                result = [
                    TextContent(
                        type="text",
                        text=f"❌ Unknown tool: {name}",
                    )
                ]

            logger.info("tool_call_completed", tool=name, success=True)
            return result

        except Exception as e:
            # Comprehensive error logging
            logger.error(
                "tool_call_failed",
                tool=name,
                error_type=type(e).__name__,
                error=str(e),
                exc_info=True,
            )

            # Return user-friendly error message
            error_msg = f"❌ Tool '{name}' failed: {type(e).__name__}: {str(e)}"

            return [
                TextContent(
                    type="text",
                    text=error_msg,
                )
            ]


async def handle_generate_sql(arguments: dict[str, Any], ctx: Any) -> list[TextContent]:
    """
    Handle generate_sql tool call with timeout and error recovery.

    Args:
    ----------
        arguments: Tool arguments
        ctx: Server context

    Returns:
    ----------
        List of text content with SQL result
    """
    natural_language = arguments.get("natural_language")
    database = arguments.get("database")

    if not natural_language:
        return [TextContent(type="text", text="❌ Error: natural_language is required")]

    # Use default database if not specified
    if not database:
        database = ctx.config.default_database
        logger.info(
            "using_default_database",
            database=database,
        )

    logger.info(
        "generate_sql_called",
        database=database,
        query_length=len(natural_language),
    )

    try:
        # Generate SQL with timeout protection
        result = await asyncio.wait_for(
            ctx.sql_generator.generate(
                natural_language=natural_language,
                database=database,
            ),
            timeout=90.0,  # 90 second total timeout
        )

        # Format response
        response_parts = [
            f"## Generated SQL\n\n```sql\n{result.sql}\n```",
            f"\n## Explanation\n{result.explanation}",
        ]

        if result.assumptions:
            assumptions_text = "\n".join(f"- {a}" for a in result.assumptions)
            response_parts.append(f"\n## Assumptions\n{assumptions_text}")

        if result.warnings:
            warnings_text = "\n".join(f"- ⚠️ {w}" for w in result.warnings)
            response_parts.append(f"\n## Warnings\n{warnings_text}")

        response_parts.append(
            f"\n## Metadata\n- Validated: {'✅ Yes' if result.validated else '❌ No'}"
        )
        response_parts.append(f"- Method: {result.generation_method}")

        logger.info(
            "generate_sql_success",
            database=database,
            sql_length=len(result.sql),
            validated=result.validated,
        )

        return [TextContent(type="text", text="\n".join(response_parts))]

    except TimeoutError:
        error_msg = (
            "❌ SQL generation timed out (90s). "
            "The AI service may be slow or unavailable. Please try again."
        )
        logger.error("sql_generation_timeout", database=database, timeout=90.0)
        return [TextContent(type="text", text=error_msg)]

    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            "sql_generation_failed",
            database=database,
            error_type=error_type,
            error=str(e),
            exc_info=True,
        )
        return [
            TextContent(
                type="text",
                text=f"❌ SQL generation failed ({error_type}): {str(e)}",
            )
        ]


async def handle_execute_query(arguments: dict[str, Any], ctx: Any) -> list[TextContent]:
    """
    Handle execute_query tool call with timeout and error recovery.

    Args:
    ----------
        arguments: Tool arguments
        ctx: Server context

    Returns:
    ----------
        List of text content with query results
    """
    natural_language = arguments.get("natural_language")
    database = arguments.get("database")
    limit = arguments.get("limit", 1000)

    if not natural_language:
        return [TextContent(type="text", text="❌ Error: natural_language is required")]

    # Use default database if not specified
    if not database:
        database = ctx.config.default_database
        logger.info(
            "using_default_database",
            database=database,
        )

    # Enforce max limit
    if limit > 10000:
        limit = 10000

    logger.info(
        "execute_query_called",
        database=database,
        query_length=len(natural_language),
        limit=limit,
    )

    try:
        # Execute query with timeout protection
        result = await asyncio.wait_for(
            ctx.query_executor.execute(
                natural_language=natural_language,
                database=database,
                limit=limit,
            ),
            timeout=120.0,  # 120 second total timeout (generation + execution)
        )

        # Format response
        response_parts = [
            f"## Executed SQL\n\n```sql\n{result.sql}\n```",
            f"\n## Results\n- Rows returned: {result.row_count}",
            f"- Execution time: {result.execution_time_ms:.2f}ms",
        ]

        if result.truncated:
            response_parts.append(f"- ⚠️ Results truncated to {limit} rows")

        # Format column information
        if result.columns:
            columns_text = ", ".join(f"`{col.name}` ({col.type})" for col in result.columns)
            response_parts.append(f"- Columns: {columns_text}")

        # Format row data (limit to first 10 rows for display)
        if result.rows:
            response_parts.append("\n### Data Preview (first 10 rows)\n")
            display_rows = result.rows[:10]

            # Create markdown table
            if display_rows and result.columns:
                # Header
                headers = [col.name for col in result.columns]
                response_parts.append("| " + " | ".join(headers) + " |")
                response_parts.append("| " + " | ".join(["---"] * len(headers)) + " |")

                # Rows
                for row in display_rows:
                    values = [str(row.get(col.name, "NULL")) for col in result.columns]
                    response_parts.append("| " + " | ".join(values) + " |")

                if result.row_count > 10:
                    response_parts.append(f"\n*... and {result.row_count - 10} more rows*")
        else:
            response_parts.append("\n*No rows returned*")

        logger.info(
            "execute_query_success",
            database=database,
            row_count=result.row_count,
            execution_time_ms=result.execution_time_ms,
        )

        return [TextContent(type="text", text="\n".join(response_parts))]

    except TimeoutError:
        error_msg = (
            "❌ Query execution timed out (120s). "
            "The query may be too complex or the AI service is slow. Please try again."
        )
        logger.error("query_execution_timeout", database=database, timeout=120.0)
        return [TextContent(type="text", text=error_msg)]

    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            "query_execution_failed",
            database=database,
            error_type=error_type,
            error=str(e),
            exc_info=True,
        )
        return [
            TextContent(
                type="text",
                text=f"❌ Query execution failed ({error_type}): {str(e)}",
            )
        ]


async def handle_list_databases(ctx: Any) -> list[TextContent]:
    """
    Handle list_databases tool call with error recovery.

    Args:
    ----------
        ctx: Server context

    Returns:
    ----------
        List of text content with database information
    """
    logger.info("list_databases_called")

    try:
        databases = ctx.schema_cache.list_databases()
        default_database = ctx.config.default_database

        if not databases:
            return [TextContent(type="text", text="⚠️ No databases configured")]

        response_parts = ["## Configured Databases\n"]

        for db_name in databases:
            # Check if this is the default database
            is_default = db_name == default_database
            default_marker = " **[DEFAULT]**" if is_default else ""

            try:
                schema = await ctx.schema_cache.get_schema(db_name)
                
                # Check connection status
                try:
                    pool = await ctx.pool_manager.get_pool(db_name)
                    pool_size = pool.get_size() if hasattr(pool, 'get_size') else "N/A"
                    pool_max = pool.get_max_size() if hasattr(pool, 'get_max_size') else "N/A"
                    connection_status = f"✅ Connected ({pool_size}/{pool_max} connections)"
                except Exception as pool_error:
                    logger.debug(
                        "pool_status_check_failed",
                        database=db_name,
                        error=str(pool_error),
                    )
                    connection_status = "⚠️ Pool unavailable"
                
                if schema:
                    table_count = len(schema.tables)
                    table_names = ", ".join(list(schema.tables.keys())[:5])
                    if len(schema.tables) > 5:
                        table_names += f", ... (+{len(schema.tables) - 5} more)"

                    response_parts.append(f"\n### {db_name}{default_marker}")
                    response_parts.append(f"- Status: {connection_status}")
                    response_parts.append(f"- Tables: {table_count}")
                    response_parts.append(f"- Sample tables: {table_names}")
                    response_parts.append(
                        f"- Last updated: {schema.last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                else:
                    response_parts.append(f"\n### {db_name}{default_marker}")
                    response_parts.append(f"- Status: {connection_status}")
                    response_parts.append("- Schema: ⚠️ Not loaded")
            except Exception as e:
                logger.warning(
                    "get_schema_failed",
                    database=db_name,
                    error=str(e),
                )
                response_parts.append(f"\n### {db_name}{default_marker}")
                response_parts.append(f"- Status: ❌ Error: {str(e)}")

        logger.info("list_databases_success", database_count=len(databases))
        return [TextContent(type="text", text="\n".join(response_parts))]

    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            "list_databases_failed",
            error_type=error_type,
            error=str(e),
            exc_info=True,
        )
        return [
            TextContent(
                type="text",
                text=f"❌ Failed to list databases ({error_type}): {str(e)}",
            )
        ]


async def handle_refresh_schema(arguments: dict[str, Any], ctx: Any) -> list[TextContent]:
    """
    Handle refresh_schema tool call with error recovery.

    Args:
    ----------
        arguments: Tool arguments
        ctx: Server context

    Returns:
    ----------
        List of text content with refresh result
    """
    database = arguments.get("database")

    if database:
        logger.info("refresh_schema_called", database=database)
        try:
            await ctx.schema_cache.refresh_schema(database)
            logger.info("refresh_schema_success", database=database)
            return [
                TextContent(
                    type="text",
                    text=f"✅ Schema refreshed successfully for database: {database}",
                )
            ]
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                "schema_refresh_failed",
                database=database,
                error_type=error_type,
                error=str(e),
                exc_info=True,
            )
            return [
                TextContent(
                    type="text",
                    text=f"❌ Failed to refresh schema for {database} ({error_type}): {str(e)}",
                )
            ]
    else:
        logger.info("refresh_all_schemas_called")
        try:
            await ctx.schema_cache.refresh_all_schemas()
            logger.info("refresh_all_schemas_success")
            return [
                TextContent(
                    type="text",
                    text="✅ All schemas refreshed successfully",
                )
            ]
        except Exception as e:
            error_type = type(e).__name__
            logger.error(
                "refresh_all_schemas_failed",
                error_type=error_type,
                error=str(e),
                exc_info=True,
            )
            return [
                TextContent(
                    type="text",
                    text=f"❌ Failed to refresh schemas ({error_type}): {str(e)}",
                )
            ]


async def handle_query_history(arguments: dict[str, Any], ctx: Any) -> list[TextContent]:
    """
    Handle query_history tool call to retrieve query execution logs.

    Args:
    ----------
        arguments: Tool arguments (database, status, limit)
        ctx: Server context

    Returns:
    ----------
        List of text content with formatted query history
    """
    database_filter = arguments.get("database")
    status_filter = arguments.get("status")
    limit = arguments.get("limit", 50)

    logger.info(
        "query_history_called",
        database=database_filter,
        status=status_filter,
        limit=limit,
    )

    try:
        if not ctx.jsonl_writer:
            return [
                TextContent(
                    type="text",
                    text="⚠️ Query history logging is not enabled",
                )
            ]

        # Read log files from the log directory
        import json

        log_dir = ctx.jsonl_writer.log_directory
        log_files = sorted(
            log_dir.glob("query_history_*.jsonl"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,  # Newest first
        )

        if not log_files:
            return [
                TextContent(
                    type="text",
                    text="⚠️ No query history found",
                )
            ]

        # Parse and filter log entries
        entries = []
        for log_file in log_files:
            if len(entries) >= limit:
                break

            try:
                with log_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        if len(entries) >= limit:
                            break

                        line = line.strip()
                        if not line:
                            continue

                        try:
                            entry = json.loads(line)

                            # Apply filters
                            if database_filter and entry.get("database") != database_filter:
                                continue

                            if status_filter and entry.get("status") != status_filter:
                                continue

                            entries.append(entry)

                        except json.JSONDecodeError:
                            logger.warning("invalid_jsonl_line", log_file=str(log_file))
                            continue

            except Exception as e:
                logger.warning(
                    "log_file_read_error",
                    log_file=str(log_file),
                    error=str(e),
                )
                continue

        if not entries:
            filter_desc = []
            if database_filter:
                filter_desc.append(f"database={database_filter}")
            if status_filter:
                filter_desc.append(f"status={status_filter}")

            filter_text = f" (filters: {', '.join(filter_desc)})" if filter_desc else ""
            return [
                TextContent(
                    type="text",
                    text=f"⚠️ No query history found matching criteria{filter_text}",
                )
            ]

        # Sort entries by timestamp (newest first)
        entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

        # Format response
        response_parts = [f"## Query History (last {len(entries)} entries)\n"]

        for i, entry in enumerate(entries[:limit], 1):
            timestamp = entry.get("timestamp", "N/A")
            database = entry.get("database", "N/A")
            status = entry.get("status", "unknown")
            nl_query = entry.get("natural_language", "N/A")
            sql = entry.get("sql", "N/A")
            exec_time = entry.get("execution_time_ms", "N/A")
            row_count = entry.get("row_count", "N/A")
            error = entry.get("error_message")

            # Format status with emoji
            status_icon = {
                "success": "✅",
                "validation_failed": "⚠️",
                "execution_failed": "❌",
                "ai_failed": "🔴",
                "template_matched": "📋",
            }.get(status, "❓")

            response_parts.append(f"\n### Entry {i}")
            response_parts.append(f"- **Time**: {timestamp}")
            response_parts.append(f"- **Database**: {database}")
            response_parts.append(f"- **Status**: {status_icon} {status}")
            response_parts.append(f"- **Query**: {nl_query}")

            if sql and sql != "N/A":
                sql_display = f"`{sql[:100]}...`" if len(sql) > 100 else f"`{sql}`"
                response_parts.append(f"- **SQL**: {sql_display}")

            if exec_time != "N/A":
                if isinstance(exec_time, int | float):
                    time_display = f"{exec_time:.2f}ms"
                else:
                    time_display = f"{exec_time}ms"
                response_parts.append(f"- **Execution Time**: {time_display}")

            if row_count != "N/A":
                response_parts.append(f"- **Rows**: {row_count}")

            if error:
                response_parts.append(f"- **Error**: {error}")

        logger.info(
            "query_history_success",
            entries_count=len(entries),
            database=database_filter,
            status=status_filter,
        )

        return [TextContent(type="text", text="\n".join(response_parts))]

    except Exception as e:
        error_type = type(e).__name__
        logger.error(
            "query_history_failed",
            error_type=error_type,
            error=str(e),
            exc_info=True,
        )
        return [
            TextContent(
                type="text",
                text=f"❌ Failed to retrieve query history ({error_type}): {str(e)}",
            )
        ]
