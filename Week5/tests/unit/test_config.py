"""
Tests for configuration loading and validation.

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

from pathlib import Path

import pytest
import yaml

from postgres_mcp.config import Config


def _write_config(path: Path, data: dict) -> None:
    """
    Write configuration data to a YAML file.

    Args:
    ----------
        path: Target YAML path.
        data: Configuration data mapping.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    path.write_text(yaml.safe_dump(data))


def _base_config() -> dict:
    """
    Build a minimal valid configuration payload.

    Args:
    ----------
        None

    Returns:
    ----------
        Base configuration mapping.

    Raises:
    ----------
        None
    """

    return {
        "server": {"name": "postgres-mcp", "version": "0.1.0"},
        "databases": [
            {
                "name": "primary",
                "host": "localhost",
                "port": 5432,
                "database": "app",
                "user": "readonly",
                "password_env_var": "PRIMARY_DB_PASSWORD",
                "ssl_mode": "prefer",
                "min_pool_size": 1,
                "max_pool_size": 2,
            },
            {
                "name": "analytics",
                "host": "localhost",
                "port": 5432,
                "database": "analytics",
                "user": "readonly",
                "password_env_var": "ANALYTICS_DB_PASSWORD",
                "ssl_mode": "prefer",
                "min_pool_size": 1,
                "max_pool_size": 2,
            },
        ],
        "default_database": "primary",
        "openai": {"api_key_env_var": "OPENAI_API_KEY", "model": "gpt-4o-mini-2024-07-18"},
    }


def test_config_load_applies_defaults(tmp_path: Path) -> None:
    """
    Ensure default values are applied when omitted from YAML.

    Args:
    ----------
        tmp_path: Temporary directory path.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    config_path = tmp_path / "config.yaml"
    _write_config(config_path, _base_config())

    config = Config.load(config_path)

    assert config.schema_cache.poll_interval_minutes == 5
    assert config.query.default_limit == 1000
    assert config.templates.enabled is True


def test_config_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """
    Ensure environment variables override YAML values.

    Args:
    ----------
        monkeypatch: Pytest monkeypatch fixture.
        tmp_path: Temporary directory path.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    config_path = tmp_path / "config.yaml"
    _write_config(config_path, _base_config())

    monkeypatch.setenv("POSTGRES_MCP_DEFAULT_DATABASE", "analytics")
    monkeypatch.setenv("POSTGRES_MCP_OPENAI__MODEL", "gpt-4o-mini-test")

    config = Config.load(config_path)

    assert config.default_database == "analytics"
    assert config.openai.model == "gpt-4o-mini-test"


def test_config_load_missing_file_raises(tmp_path: Path) -> None:
    """
    Ensure missing config file raises a FileNotFoundError.

    Args:
    ----------
        tmp_path: Temporary directory path.

    Returns:
    ----------
        None

    Raises:
    ----------
        None
    """

    missing_path = tmp_path / "missing.yaml"

    with pytest.raises(FileNotFoundError):
        Config.load(missing_path)
