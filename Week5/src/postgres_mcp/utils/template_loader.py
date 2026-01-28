"""
Template loader for loading query templates from YAML files.

This module provides functionality to load, parse, and validate SQL query
templates from YAML files.
"""

from __future__ import annotations

from pathlib import Path

import structlog
import yaml

from postgres_mcp.models.template import QueryTemplate

logger = structlog.get_logger(__name__)


class TemplateLoadError(Exception):
    """Raised when template loading fails."""

    pass


class TemplateLoader:
    """
    Load query templates from YAML files.

    Args:
    ----------
        template_dir: Directory containing template YAML files.

    Returns:
    ----------
        None

    Raises:
    ----------
        TemplateLoadError: If template directory does not exist.

    Example:
    ----------
        >>> loader = TemplateLoader(Path("templates/queries"))
        >>> templates = loader.load_all()
        >>> print(f"Loaded {len(templates)} templates")
    """

    def __init__(self, template_dir: Path) -> None:
        """Initialize template loader."""
        if not template_dir.exists():
            raise TemplateLoadError(f"template directory does not exist: {template_dir}")
        if not template_dir.is_dir():
            raise TemplateLoadError(f"template path is not a directory: {template_dir}")

        self.template_dir = template_dir
        logger.info("template_loader_initialized", template_dir=str(template_dir))

    def load_all(self) -> list[QueryTemplate]:
        """
        Load all templates from the template directory.

        Returns:
        ----------
            List of loaded templates sorted by priority (descending).

        Raises:
        ----------
            TemplateLoadError: If template loading or validation fails.

        Example:
        ----------
            >>> templates = loader.load_all()
            >>> for template in templates:
            ...     print(f"{template.name}: {template.priority}")
        """
        templates: list[QueryTemplate] = []
        yaml_files = list(self.template_dir.glob("*.yaml")) + list(self.template_dir.glob("*.yml"))

        if not yaml_files:
            logger.warning("no_template_files_found", template_dir=str(self.template_dir))
            return templates

        for yaml_file in yaml_files:
            try:
                template = self._load_template(yaml_file)
                templates.append(template)
                logger.debug("template_loaded", template_name=template.name, file=yaml_file.name)
            except Exception as e:
                logger.error(
                    "template_load_failed",
                    file=yaml_file.name,
                    error=str(e),
                    exc_info=True,
                )
                raise TemplateLoadError(
                    f"failed to load template from {yaml_file.name}: {e}"
                ) from e

        # Sort by priority (descending) so higher priority templates are matched first
        templates.sort(key=lambda t: t.priority, reverse=True)

        logger.info("templates_loaded", count=len(templates))
        return templates

    def _load_template(self, yaml_file: Path) -> QueryTemplate:
        """
        Load a single template from a YAML file.

        Args:
        ----------
            yaml_file: Path to YAML file.

        Returns:
        ----------
            Parsed and validated QueryTemplate.

        Raises:
        ----------
            TemplateLoadError: If YAML parsing or validation fails.
        """
        try:
            with yaml_file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise TemplateLoadError(f"YAML parsing failed: {e}") from e
        except OSError as e:
            raise TemplateLoadError(f"file read failed: {e}") from e

        if not isinstance(data, dict):
            raise TemplateLoadError(f"template must be a YAML dictionary, got {type(data)}")

        try:
            template = QueryTemplate(**data)
        except Exception as e:
            raise TemplateLoadError(f"template validation failed: {e}") from e

        return template

    def reload(self) -> list[QueryTemplate]:
        """
        Reload all templates from disk.

        This is useful for development or dynamic template updates.

        Returns:
        ----------
            List of reloaded templates sorted by priority (descending).

        Raises:
        ----------
            TemplateLoadError: If template loading or validation fails.
        """
        logger.info("reloading_templates", template_dir=str(self.template_dir))
        return self.load_all()

    def load_template_by_name(self, name: str) -> QueryTemplate | None:
        """
        Load a specific template by name.

        Args:
        ----------
            name: Template name (without .yaml extension).

        Returns:
        ----------
            Loaded template or None if not found.

        Raises:
        ----------
            TemplateLoadError: If template loading or validation fails.

        Example:
        ----------
            >>> template = loader.load_template_by_name("select_all")
            >>> if template:
            ...     print(f"Loaded: {template.description}")
        """
        yaml_file = self.template_dir / f"{name}.yaml"
        if not yaml_file.exists():
            yaml_file = self.template_dir / f"{name}.yml"
            if not yaml_file.exists():
                logger.warning("template_not_found", template_name=name)
                return None

        try:
            template = self._load_template(yaml_file)
            logger.debug("template_loaded_by_name", template_name=name)
            return template
        except Exception as e:
            logger.error("template_load_by_name_failed", template_name=name, error=str(e))
            raise
