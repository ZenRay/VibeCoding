"""
MCP resources implementation.

Implements schema resources for database metadata access.
"""

import structlog
from mcp.server import Server
from mcp.types import Resource

logger = structlog.get_logger(__name__)


def register_resources(server: Server) -> None:
    """
    Register all MCP resources with the server.

    Args:
    ----------
        server: MCP Server instance
    """

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """
        List all available resources.

        Returns:
        ----------
            List of resource definitions
        """
        from postgres_mcp.server import get_context
        
        ctx = get_context()
        resources: list[Resource] = []

        # Get all databases
        databases = ctx.schema_cache.list_databases()

        # Add database-level resources
        for db_name in databases:
            resources.append(
                Resource(
                    uri=f"schema://{db_name}",
                    name=f"Schema for {db_name}",
                    description=f"Complete schema information for database: {db_name}",
                    mimeType="text/plain",
                )
            )

            # Get schema to list tables
            schema = await ctx.schema_cache.get_schema(db_name)
            if schema:
                for table_name in schema.tables.keys():
                    resources.append(
                        Resource(
                            uri=f"schema://{db_name}/{table_name}",
                            name=f"Table {db_name}.{table_name}",
                            description=f"Schema for table {table_name} in database {db_name}",
                            mimeType="text/plain",
                        )
                    )

        return resources

    @server.read_resource()
    async def read_resource(uri: str) -> str:
        """
        Read resource content by URI.

        Args:
        ----------
            uri: Resource URI (schema://{database} or schema://{database}/{table})

        Returns:
        ----------
            Resource content as text
        """
        from postgres_mcp.server import get_context
        
        ctx = get_context()

        try:
            # Parse URI: schema://{database}/{table?}
            if not uri.startswith("schema://"):
                return f"Invalid URI scheme: {uri}"

            path = uri[9:]  # Remove "schema://"
            parts = path.split("/")

            if len(parts) == 1:
                # Database-level resource
                return await read_database_schema(parts[0], ctx)
            elif len(parts) == 2:
                # Table-level resource
                return await read_table_schema(parts[0], parts[1], ctx)
            else:
                return f"Invalid URI format: {uri}"

        except Exception as e:
            logger.error("resource_read_failed", uri=uri, error=str(e))
            return f"Error reading resource: {str(e)}"


async def read_database_schema(database: str, ctx) -> str:
    """
    Read complete database schema.

    Args:
    ----------
        database: Database name
        ctx: Server context

    Returns:
    ----------
        Formatted database schema
    """
    logger.info("read_database_schema", database=database)

    schema = await ctx.schema_cache.get_schema(database)
    if not schema:
        return f"Database not found: {database}"

    # Format schema as DDL
    lines = [
        f"# Database Schema: {database}",
        f"\n**Last Updated**: {schema.last_updated.strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Tables**: {len(schema.tables)}",
        "\n---\n",
    ]

    # Add each table
    for table_name, table in schema.tables.items():
        lines.append(f"\n## Table: {table_name}\n")
        lines.append("### Columns\n")

        for col in table.columns:
            col_info = f"- `{col.name}` {col.data_type}"
            if col.primary_key:
                col_info += " **[PK]**"
            if not col.nullable:
                col_info += " NOT NULL"
            if col.default:
                col_info += f" DEFAULT {col.default}"
            lines.append(col_info)

        # Indexes
        if table.indexes:
            lines.append("\n### Indexes\n")
            for idx in table.indexes:
                idx_type = "UNIQUE" if idx.unique else "INDEX"
                lines.append(f"- {idx_type}: `{idx.name}` on {', '.join(idx.columns)}")

        # Foreign keys
        if table.foreign_keys:
            lines.append("\n### Foreign Keys\n")
            for fk in table.foreign_keys:
                lines.append(f"- `{fk.column}` → `{fk.foreign_table}.{fk.foreign_column}`")

        lines.append("\n---\n")

    return "\n".join(lines)


async def read_table_schema(database: str, table: str, ctx) -> str:
    """
    Read specific table schema.

    Args:
    ----------
        database: Database name
        table: Table name
        ctx: Server context

    Returns:
    ----------
        Formatted table schema
    """
    logger.info("read_table_schema", database=database, table=table)

    schema = await ctx.schema_cache.get_schema(database)
    if not schema:
        return f"Database not found: {database}"

    table_schema = schema.tables.get(table)
    if not table_schema:
        return f"Table not found: {database}.{table}"

    # Format table schema
    lines = [
        f"# Table: {database}.{table}",
        "\n## Columns\n",
    ]

    # Column details
    for col in table_schema.columns:
        lines.append(f"### {col.name}\n")
        lines.append(f"- **Type**: {col.data_type}")
        lines.append(f"- **Nullable**: {'Yes' if col.nullable else 'No'}")
        if col.primary_key:
            lines.append("- **Primary Key**: Yes")
        if col.default:
            lines.append(f"- **Default**: {col.default}")
        lines.append("")

    # Indexes
    if table_schema.indexes:
        lines.append("## Indexes\n")
        for idx in table_schema.indexes:
            idx_type = "UNIQUE INDEX" if idx.unique else "INDEX"
            lines.append(f"### {idx.name}")
            lines.append(f"- **Type**: {idx_type}")
            lines.append(f"- **Columns**: {', '.join(idx.columns)}")
            lines.append("")

    # Foreign keys
    if table_schema.foreign_keys:
        lines.append("## Foreign Keys\n")
        for fk in table_schema.foreign_keys:
            lines.append(f"### {fk.name}")
            lines.append(f"- **Column**: {fk.column}")
            lines.append(f"- **References**: {fk.foreign_table}.{fk.foreign_column}")
            lines.append("")

    # Generate DDL
    lines.append("## DDL\n")
    lines.append("```sql")
    lines.append(schema.to_ddl(table_names=[table]))
    lines.append("```")

    return "\n".join(lines)
