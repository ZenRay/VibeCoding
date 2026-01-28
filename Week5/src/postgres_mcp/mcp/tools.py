"""
MCP tools implementation.

Implements all MCP tools for PostgreSQL operations.
"""

from typing import Any

import structlog
from mcp.server import Server
from mcp.types import TextContent, Tool

from postgres_mcp.server import get_context

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
                            "description": "Target database name",
                        },
                    },
                    "required": ["natural_language", "database"],
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
                            "description": "Target database name",
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum rows to return (default: 1000, max: 10000)",
                            "minimum": 1,
                            "maximum": 10000,
                        },
                    },
                    "required": ["natural_language", "database"],
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
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """
        Handle tool calls.

        Args:
        ----------
            name: Tool name
            arguments: Tool arguments

        Returns:
        ----------
            List of text content responses
        """
        ctx = get_context()

        try:
            if name == "generate_sql":
                return await handle_generate_sql(arguments, ctx)
            elif name == "execute_query":
                return await handle_execute_query(arguments, ctx)
            elif name == "list_databases":
                return await handle_list_databases(ctx)
            elif name == "refresh_schema":
                return await handle_refresh_schema(arguments, ctx)
            else:
                return [
                    TextContent(
                        type="text",
                        text=f"Unknown tool: {name}",
                    )
                ]

        except Exception as e:
            logger.error("tool_call_failed", tool=name, error=str(e))
            return [
                TextContent(
                    type="text",
                    text=f"Error: {str(e)}",
                )
            ]


async def handle_generate_sql(arguments: dict[str, Any], ctx: Any) -> list[TextContent]:
    """
    Handle generate_sql tool call.

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
        return [TextContent(type="text", text="Error: natural_language is required")]

    if not database:
        return [TextContent(type="text", text="Error: database is required")]

    logger.info(
        "generate_sql_called",
        database=database,
        query_length=len(natural_language),
    )

    try:
        # Generate SQL
        result = await ctx.sql_generator.generate(
            natural_language=natural_language,
            database=database,
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

        return [TextContent(type="text", text="\n".join(response_parts))]

    except Exception as e:
        logger.error("sql_generation_failed", error=str(e))
        return [
            TextContent(
                type="text",
                text=f"❌ SQL generation failed: {str(e)}",
            )
        ]


async def handle_execute_query(arguments: dict[str, Any], ctx: Any) -> list[TextContent]:
    """
    Handle execute_query tool call.

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
        return [TextContent(type="text", text="Error: natural_language is required")]

    if not database:
        return [TextContent(type="text", text="Error: database is required")]

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
        # Execute query
        result = await ctx.query_executor.execute(
            natural_language=natural_language,
            database=database,
            limit=limit,
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

        return [TextContent(type="text", text="\n".join(response_parts))]

    except Exception as e:
        logger.error("query_execution_failed", error=str(e))
        return [
            TextContent(
                type="text",
                text=f"❌ Query execution failed: {str(e)}",
            )
        ]


async def handle_list_databases(ctx: Any) -> list[TextContent]:
    """
    Handle list_databases tool call.

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

        if not databases:
            return [TextContent(type="text", text="No databases configured")]

        response_parts = ["## Configured Databases\n"]

        for db_name in databases:
            schema = await ctx.schema_cache.get_schema(db_name)
            if schema:
                table_count = len(schema.tables)
                table_names = ", ".join(list(schema.tables.keys())[:5])
                if len(schema.tables) > 5:
                    table_names += f", ... (+{len(schema.tables) - 5} more)"

                response_parts.append(f"\n### {db_name}")
                response_parts.append(f"- Tables: {table_count}")
                response_parts.append(f"- Sample tables: {table_names}")
                response_parts.append(
                    f"- Last updated: {schema.last_updated.strftime('%Y-%m-%d %H:%M:%S')}"
                )
            else:
                response_parts.append(f"\n### {db_name}")
                response_parts.append("- Status: Schema not loaded")

        return [TextContent(type="text", text="\n".join(response_parts))]

    except Exception as e:
        logger.error("list_databases_failed", error=str(e))
        return [
            TextContent(
                type="text",
                text=f"❌ Failed to list databases: {str(e)}",
            )
        ]


async def handle_refresh_schema(arguments: dict[str, Any], ctx: Any) -> list[TextContent]:
    """
    Handle refresh_schema tool call.

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
            return [
                TextContent(
                    type="text",
                    text=f"✅ Schema refreshed successfully for database: {database}",
                )
            ]
        except Exception as e:
            logger.error("schema_refresh_failed", database=database, error=str(e))
            return [
                TextContent(
                    type="text",
                    text=f"❌ Failed to refresh schema for {database}: {str(e)}",
                )
            ]
    else:
        logger.info("refresh_all_schemas_called")
        try:
            await ctx.schema_cache.refresh_all_schemas()
            return [
                TextContent(
                    type="text",
                    text="✅ All schemas refreshed successfully",
                )
            ]
        except Exception as e:
            logger.error("refresh_all_schemas_failed", error=str(e))
            return [
                TextContent(
                    type="text",
                    text=f"❌ Failed to refresh schemas: {str(e)}",
                )
            ]
