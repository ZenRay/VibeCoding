"""
Database connection configuration models.

This module defines models for database connection settings,
connection status, and validation rules.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ConnectionStatus(str, Enum):
    """Connection status for database pools."""

    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class ConnectionType(str, Enum):
    """Connection types for database configuration."""

    PRECONFIGURED = "preconfigured"
    DYNAMIC = "dynamic"


class DatabaseConnection(BaseModel, frozen=True):
    """
    Database connection settings.

    Args:
    ----------
        name: Connection name identifier.
        host: Database host.
        port: Database port.
        database: Database name.
        user: Database user.
        password_env_var: Environment variable holding the password.
        ssl_mode: SSL mode for the connection.
        min_pool_size: Minimum pool size.
        max_pool_size: Maximum pool size.
        connection_type: Connection type (preconfigured or dynamic).

    Returns:
    ----------
        None

    Raises:
    ----------
        ValueError: If validation rules are violated.
    """

    name: str = Field(..., min_length=1, max_length=64)
    host: str = Field(..., min_length=1)
    port: int = Field(5432, ge=1, le=65535)
    database: str = Field(..., min_length=1)
    user: str = Field(..., min_length=1)
    password_env_var: str = Field(..., min_length=1)
    ssl_mode: str = Field("prefer", pattern="^(disable|allow|prefer|require)$")
    min_pool_size: int = Field(5, ge=1, le=50)
    max_pool_size: int = Field(20, ge=1, le=100)
    connection_type: ConnectionType = ConnectionType.PRECONFIGURED

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Validate connection name format.

        Args:
        ----------
            value: Name to validate.

        Returns:
        ----------
            The validated name.

        Raises:
        ----------
            ValueError: If the name contains invalid characters.
        """

        if not value.replace("_", "").replace("-", "").isalnum():
            raise ValueError("name must contain only letters, numbers, '_' or '-'")
        return value

    @field_validator("max_pool_size")
    @classmethod
    def validate_pool_sizes(cls, value: int, info) -> int:
        """
        Validate pool size constraints.

        Args:
        ----------
            value: Maximum pool size to validate.
            info: Pydantic validation info.

        Returns:
        ----------
            The validated pool size.

        Raises:
        ----------
            ValueError: If max_pool_size is smaller than min_pool_size.
        """

        min_size = info.data.get("min_pool_size", 5)
        if value < min_size:
            raise ValueError(f"max_pool_size ({value}) must be >= min_pool_size ({min_size})")
        return value
