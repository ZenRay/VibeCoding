"""
Application configuration models and loaders.

Args:
----------
    None

Returns:
----------
    None

Raises:
----------
    FileNotFoundError: If the configuration file does not exist.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from postgres_mcp.models.connection import DatabaseConnection


class ServerConfig(BaseModel):
    """
    Server metadata configuration.

    Args:
    ----------
        name: Server name.
        version: Server version string.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    name: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)


class OpenAIConfig(BaseModel):
    """
    OpenAI configuration settings.

    Args:
    ----------
        api_key_env_var: Environment variable containing API key.
        model: OpenAI model identifier.
        temperature: Sampling temperature.
        max_tokens: Maximum tokens to generate.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    api_key_env_var: str = Field(..., min_length=1)
    model: str = Field(..., min_length=1)
    temperature: float = Field(0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(1000, ge=1)


class SchemaCacheConfig(BaseModel):
    """
    Schema cache behavior configuration.

    Args:
    ----------
        poll_interval_minutes: Refresh interval in minutes.
        load_sample_data: Whether to include sample data.
        max_sample_rows: Maximum sample rows per table.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    poll_interval_minutes: int = Field(5, ge=1)
    load_sample_data: bool = True
    max_sample_rows: int = Field(3, ge=0, le=10)


class QueryConfig(BaseModel):
    """
    Query execution configuration.

    Args:
    ----------
        default_limit: Default row limit for queries.
        max_timeout_seconds: Maximum query timeout.
        enable_result_validation: Whether to validate results.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    default_limit: int = Field(1000, ge=1)
    max_timeout_seconds: int = Field(30, ge=1)
    enable_result_validation: bool = False


class TemplateConfig(BaseModel):
    """
    Template fallback configuration.

    Args:
    ----------
        enabled: Whether template fallback is enabled.
        directory: Directory containing template definitions.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    enabled: bool = True
    directory: str = "src/postgres_mcp/templates/queries"


class LoggingConfig(BaseModel):
    """
    Logging configuration settings.

    Args:
    ----------
        level: Log level string.
        directory: Log directory path.
        retention_days: Days to retain log files.
        max_file_size_mb: Maximum file size before rotation.
        buffer_size: Buffer size for JSONL logging.
        flush_interval_seconds: Flush interval in seconds.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    level: str = Field("INFO", min_length=1)
    directory: str = "logs/queries"
    retention_days: int = Field(30, ge=1)
    max_file_size_mb: int = Field(100, ge=1)
    buffer_size: int = Field(100, ge=1)
    flush_interval_seconds: float = Field(5.0, ge=0.1)


class Config(BaseSettings):
    """
    Application configuration root.

    Args:
    ----------
        server: Server configuration.
        databases: Database connection configurations.
        default_database: Default database name.
        openai: OpenAI settings.
        schema_cache: Schema cache settings.
        query: Query execution settings.
        templates: Template settings.
        logging: Logging settings.

    Returns:
    ----------
        None

    Raises:
    ----------
        ValueError: If default database is not defined in databases.
    """

    model_config = SettingsConfigDict(
        env_prefix="POSTGRES_MCP_",
        env_nested_delimiter="__",
        extra="forbid",
    )

    server: ServerConfig
    databases: list[DatabaseConnection]
    default_database: str
    openai: OpenAIConfig
    schema_cache: SchemaCacheConfig = Field(default_factory=SchemaCacheConfig)
    query: QueryConfig = Field(default_factory=QueryConfig)
    templates: TemplateConfig = Field(default_factory=TemplateConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @model_validator(mode="after")
    def validate_default_database(self) -> Config:
        """
        Ensure default database exists in configuration.

        Args:
        ----------
            self: Config instance to validate.

        Returns:
        ----------
            The validated Config instance.

        Raises:
        ----------
            ValueError: If default_database is not present in databases.
        """

        names = {db.name for db in self.databases}
        if self.default_database not in names:
            raise ValueError("default_database must match a configured database name")
        return self

    @classmethod
    def load(cls, path: Path | str | None = None) -> Config:
        """
        Load configuration from a YAML file with environment overrides.

        Args:
        ----------
            path: Optional path to the YAML configuration file.

        Returns:
        ----------
            Loaded Config instance.

        Raises:
        ----------
            FileNotFoundError: If the configuration file does not exist.
        """

        config_path = Path(path) if path is not None else Path("config/config.yaml")
        if not config_path.exists():
            raise FileNotFoundError(f"config file not found: {config_path}")

        data = yaml.safe_load(config_path.read_text()) or {}
        if not isinstance(data, dict):
            raise ValueError("config file must contain a YAML mapping")

        merged = _apply_env_overrides(data)
        return cls(**merged)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert configuration to a dictionary.

        Args:
        ----------
            None

        Returns:
        ----------
            Configuration as a dictionary.

        Raises:
        ----------
            None
        """

        return self.model_dump()


def _apply_env_overrides(data: dict[str, Any]) -> dict[str, Any]:
    """
    Apply environment variable overrides to config data.

    Args:
    ----------
        data: YAML configuration mapping.

    Returns:
    ----------
        Configuration mapping with env overrides applied.

    Raises:
    ----------
        None
    """

    prefix = "POSTGRES_MCP_"
    overrides: dict[str, Any] = {}
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        path = key[len(prefix) :].lower().split("__")
        cursor: dict[str, Any] = overrides
        for part in path[:-1]:
            cursor = cursor.setdefault(part, {})
        cursor[path[-1]] = value

    return _deep_merge(data, overrides)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """
    Merge override mapping into base mapping.

    Args:
    ----------
        base: Base mapping.
        override: Override mapping.

    Returns:
    ----------
        Merged mapping.

    Raises:
    ----------
        None
    """

    merged: dict[str, Any] = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged
