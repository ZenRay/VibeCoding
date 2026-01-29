"""
Schema cache models for database metadata.

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

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, computed_field


class ColumnSchema(BaseModel, frozen=True):
    """
    Column schema details.

    Args:
    ----------
        name: Column name.
        data_type: PostgreSQL data type name.
        nullable: Whether the column allows NULL values.
        primary_key: Whether the column is part of the primary key.
        foreign_key_table: Referenced table name if a foreign key.
        foreign_key_column: Referenced column name if a foreign key.
        default_value: Default value expression.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    name: str
    data_type: str
    nullable: bool = True
    primary_key: bool = False
    foreign_key_table: str | None = None
    foreign_key_column: str | None = None
    default_value: str | None = None


class IndexSchema(BaseModel, frozen=True):
    """
    Index schema details.

    Args:
    ----------
        name: Index name.
        columns: Column names in the index.
        unique: Whether the index is unique.
        index_type: Index type (btree, hash, gin, gist).

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    name: str
    columns: list[str]
    unique: bool = False
    index_type: str = "btree"


class ForeignKeySchema(BaseModel, frozen=True):
    """
    Foreign key schema details.

    Args:
    ----------
        name: Constraint name
        column: Source column name
        foreign_table: Referenced table name
        foreign_column: Referenced column name

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    name: str
    column: str
    foreign_table: str
    foreign_column: str


class TableSchema(BaseModel, frozen=True):
    """
    Table schema details.

    Args:
    ----------
        name: Table name.
        columns: Column schemas.
        indexes: Index schemas.
        foreign_keys: Foreign key schemas.
        row_count_estimate: Estimated row count.
        sample_data: Sample rows for the table.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    name: str
    columns: list[ColumnSchema]
    indexes: list[IndexSchema] = Field(default_factory=list)
    foreign_keys: list[ForeignKeySchema] = Field(default_factory=list)
    row_count_estimate: int | None = None
    sample_data: list[dict[str, Any]] = Field(default_factory=list, max_length=3)

    @computed_field
    @property
    def primary_keys(self) -> list[str]:
        """
        Compute primary key column names.

        Args:
        ----------
            None

        Returns:
        ----------
            List of primary key column names.

        Raises:
        ----------
            None
        """

        return [column.name for column in self.columns if column.primary_key]

    @computed_field
    @property
    def foreign_key_relationships(self) -> list[dict[str, str]]:
        """
        Compute foreign key relationships (compatibility property).

        Args:
        ----------
            None

        Returns:
        ----------
            List of foreign key mapping dictionaries.

        Raises:
        ----------
            None
        """

        relationships: list[dict[str, str]] = []

        # From ForeignKeySchema list
        for fk in self.foreign_keys:
            relationships.append(
                {
                    "column": fk.column,
                    "ref_table": fk.foreign_table,
                    "ref_column": fk.foreign_column,
                }
            )

        # From column-level foreign keys (backward compatibility)
        for column in self.columns:
            if column.foreign_key_table:
                relationships.append(
                    {
                        "column": column.name,
                        "ref_table": column.foreign_key_table,
                        "ref_column": column.foreign_key_column or "",
                    }
                )
        return relationships


class DatabaseSchema(BaseModel):
    """
    Database schema cache model.

    Args:
    ----------
        database_name: Database name.
        tables: Mapping of table name to schema.
        views: View names.
        custom_types: Custom type definitions.
        last_updated: Timestamp of last update.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    database_name: str
    tables: dict[str, TableSchema] = Field(default_factory=dict)
    views: list[str] = Field(default_factory=list)
    custom_types: dict[str, str] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @computed_field
    @property
    def table_count(self) -> int:
        """
        Compute table count.

        Args:
        ----------
            None

        Returns:
        ----------
            Number of tables in the schema.

        Raises:
        ----------
            None
        """

        return len(self.tables)

    def to_ddl(self, table_names: list[str] | None = None) -> str:
        """
        Render tables to a PostgreSQL DDL string.

        Args:
        ----------
            table_names: Optional list of table names to include.

        Returns:
        ----------
            DDL string for the selected tables.

        Raises:
        ----------
            None
        """

        tables_to_export = table_names or list(self.tables.keys())
        ddl_parts: list[str] = []

        for table_name in tables_to_export:
            table = self.tables.get(table_name)
            if table is None:
                continue

            column_lines: list[str] = []
            for column in table.columns:
                column_def = f"  {column.name} {column.data_type}"
                if not column.nullable:
                    column_def += " NOT NULL"
                if column.primary_key:
                    column_def += " PRIMARY KEY"
                column_lines.append(column_def)

            for fk in table.foreign_key_relationships:
                fk_def = (
                    f"  FOREIGN KEY ({fk['column']}) "
                    f"REFERENCES {fk['ref_table']}({fk['ref_column']})"
                )
                column_lines.append(fk_def)

            ddl = f"CREATE TABLE {table_name} (\n" + ",\n".join(column_lines) + "\n);"

            if table.sample_data:
                samples = [f"  {row}" for row in table.sample_data]
                ddl += f"\n-- Sample data ({len(samples)} rows):\n" + "\n".join(samples)

            ddl_parts.append(ddl)

        return "\n\n".join(ddl_parts)
