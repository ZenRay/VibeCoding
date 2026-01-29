"""
Unit tests for Template Loader.

Tests YAML template loading, parsing, and validation.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from postgres_mcp.models.template import ParameterType
from postgres_mcp.utils.template_loader import TemplateLoader, TemplateLoadError


@pytest.fixture
def temp_template_dir(tmp_path: Path) -> Path:
    """Create temporary directory for test templates."""
    template_dir = tmp_path / "templates"
    template_dir.mkdir()
    return template_dir


@pytest.fixture
def valid_template_yaml() -> dict[str, Any]:
    """Create valid template YAML content."""
    return {
        "name": "select_all",
        "description": "Select all rows from a table",
        "priority": 80,
        "keywords": ["all", "show", "list"],
        "patterns": [r"显示.*所有", r"列出.*所有"],
        "parameters": [
            {
                "name": "table",
                "type": "identifier",
                "description": "Table name",
                "required": True,
            }
        ],
        "sql_template": "SELECT * FROM {table} LIMIT 1000",
        "examples": [
            {"input": "显示所有用户", "params": {"table": "users"}},
        ],
    }


class TestTemplateLoaderBasic:
    """Test basic template loader functionality."""

    def test_initialization(self, temp_template_dir: Path) -> None:
        """Test TemplateLoader initialization."""
        loader = TemplateLoader(template_dir=temp_template_dir)
        assert loader.template_dir == temp_template_dir

    def test_load_empty_directory(self, temp_template_dir: Path) -> None:
        """Test loading from empty directory."""
        loader = TemplateLoader(template_dir=temp_template_dir)
        templates = loader.load_all()
        assert len(templates) == 0

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test with nonexistent directory."""
        nonexistent = tmp_path / "does_not_exist"
        with pytest.raises(TemplateLoadError, match="directory does not exist"):
            TemplateLoader(template_dir=nonexistent)


class TestTemplateLoaderParsing:
    """Test YAML parsing and validation."""

    def test_load_single_template(
        self,
        temp_template_dir: Path,
        valid_template_yaml: dict[str, Any],
    ) -> None:
        """Test loading a single valid template."""
        # Write template file
        template_file = temp_template_dir / "select_all.yaml"
        with template_file.open("w") as f:
            yaml.dump(valid_template_yaml, f)

        # Load templates
        loader = TemplateLoader(template_dir=temp_template_dir)
        templates = loader.load_all()

        assert len(templates) == 1
        assert templates[0].name == "select_all"
        assert templates[0].priority == 80
        assert len(templates[0].keywords) == 3

    def test_load_multiple_templates(
        self,
        temp_template_dir: Path,
        valid_template_yaml: dict[str, Any],
    ) -> None:
        """Test loading multiple template files."""
        # Create 3 template files
        template_names = ["template_a", "template_b", "template_c"]
        for name in template_names:
            template_data = valid_template_yaml.copy()
            template_data["name"] = name
            template_file = temp_template_dir / f"{name}.yaml"
            with template_file.open("w") as f:
                yaml.dump(template_data, f)

        loader = TemplateLoader(template_dir=temp_template_dir)
        templates = loader.load_all()
        assert len(templates) == 3

    def test_ignore_non_yaml_files(
        self,
        temp_template_dir: Path,
        valid_template_yaml: dict[str, Any],
    ) -> None:
        """Test that non-YAML files are ignored."""
        # Create YAML template
        yaml_file = temp_template_dir / "template.yaml"
        with yaml_file.open("w") as f:
            yaml.dump(valid_template_yaml, f)

        # Create non-YAML files
        (temp_template_dir / "readme.txt").write_text("Not a template")
        (temp_template_dir / "config.json").write_text("{}")

        loader = TemplateLoader(template_dir=temp_template_dir)
        templates = loader.load_all()
        assert len(templates) == 1

    def test_parse_parameter_types(
        self,
        temp_template_dir: Path,
    ) -> None:
        """Test parsing different parameter types."""
        template_data = {
            "name": "complex_query",
            "description": "Query with multiple parameter types",
            "priority": 70,
            "keywords": ["test"],
            "parameters": [
                {"name": "table", "type": "identifier", "description": "Table", "required": True},
                {
                    "name": "condition",
                    "type": "expression",
                    "description": "Condition",
                    "required": True,
                },
                {
                    "name": "value",
                    "type": "literal",
                    "description": "Value",
                    "required": False,
                    "default": "0",
                },
                {
                    "name": "order",
                    "type": "keyword",
                    "description": "Order",
                    "required": False,
                    "default": "ASC",
                },
            ],
            "sql_template": "SELECT * FROM {table} WHERE {condition}",
        }

        template_file = temp_template_dir / "complex.yaml"
        with template_file.open("w") as f:
            yaml.dump(template_data, f)

        loader = TemplateLoader(template_dir=temp_template_dir)
        templates = loader.load_all()

        assert len(templates) == 1
        template = templates[0]
        assert len(template.parameters) == 4
        assert template.parameters[0].type == ParameterType.IDENTIFIER
        assert template.parameters[1].type == ParameterType.EXPRESSION
        assert template.parameters[2].type == ParameterType.LITERAL
        assert template.parameters[3].type == ParameterType.KEYWORD


class TestTemplateLoaderValidation:
    """Test template validation."""

    def test_missing_required_field(
        self,
        temp_template_dir: Path,
    ) -> None:
        """Test validation error for missing required field."""
        invalid_template = {
            "name": "invalid",
            # Missing required fields: description, priority, keywords, sql_template
        }

        template_file = temp_template_dir / "invalid.yaml"
        with template_file.open("w") as f:
            yaml.dump(invalid_template, f)

        loader = TemplateLoader(template_dir=temp_template_dir)
        with pytest.raises(TemplateLoadError, match="validation failed"):
            loader.load_all()

    def test_invalid_priority_range(
        self,
        temp_template_dir: Path,
        valid_template_yaml: dict[str, Any],
    ) -> None:
        """Test validation error for priority out of range."""
        invalid_template = valid_template_yaml.copy()
        invalid_template["priority"] = 150  # Max is 100

        template_file = temp_template_dir / "invalid.yaml"
        with template_file.open("w") as f:
            yaml.dump(invalid_template, f)

        loader = TemplateLoader(template_dir=temp_template_dir)
        with pytest.raises(TemplateLoadError, match="validation failed"):
            loader.load_all()

    def test_invalid_template_name_format(
        self,
        temp_template_dir: Path,
        valid_template_yaml: dict[str, Any],
    ) -> None:
        """Test validation error for invalid template name format."""
        invalid_template = valid_template_yaml.copy()
        invalid_template["name"] = "Invalid-Name"  # Should be lowercase with underscores

        template_file = temp_template_dir / "invalid.yaml"
        with template_file.open("w") as f:
            yaml.dump(invalid_template, f)

        loader = TemplateLoader(template_dir=temp_template_dir)
        with pytest.raises(TemplateLoadError, match="validation failed"):
            loader.load_all()

    def test_empty_keywords_list(
        self,
        temp_template_dir: Path,
        valid_template_yaml: dict[str, Any],
    ) -> None:
        """Test validation error for empty keywords list."""
        invalid_template = valid_template_yaml.copy()
        invalid_template["keywords"] = []  # Must have at least 1

        template_file = temp_template_dir / "invalid.yaml"
        with template_file.open("w") as f:
            yaml.dump(invalid_template, f)

        loader = TemplateLoader(template_dir=temp_template_dir)
        with pytest.raises(TemplateLoadError, match="validation failed"):
            loader.load_all()

    def test_invalid_parameter_type(
        self,
        temp_template_dir: Path,
        valid_template_yaml: dict[str, Any],
    ) -> None:
        """Test validation error for invalid parameter type."""
        invalid_template = valid_template_yaml.copy()
        invalid_template["parameters"][0]["type"] = "invalid_type"

        template_file = temp_template_dir / "invalid.yaml"
        with template_file.open("w") as f:
            yaml.dump(invalid_template, f)

        loader = TemplateLoader(template_dir=temp_template_dir)
        with pytest.raises(TemplateLoadError, match="validation failed"):
            loader.load_all()


class TestTemplateLoaderErrorHandling:
    """Test error handling for various failure scenarios."""

    def test_malformed_yaml(
        self,
        temp_template_dir: Path,
    ) -> None:
        """Test error handling for malformed YAML."""
        template_file = temp_template_dir / "malformed.yaml"
        template_file.write_text("{ invalid yaml content [")

        loader = TemplateLoader(template_dir=temp_template_dir)
        with pytest.raises(TemplateLoadError, match="YAML parsing failed"):
            loader.load_all()

    def test_partial_failure_skip_invalid(
        self,
        temp_template_dir: Path,
        valid_template_yaml: dict[str, Any],
    ) -> None:
        """Test that valid templates load even if some are invalid."""
        # Create valid template
        valid_file = temp_template_dir / "valid.yaml"
        with valid_file.open("w") as f:
            yaml.dump(valid_template_yaml, f)

        # Create invalid template
        invalid_file = temp_template_dir / "invalid.yaml"
        invalid_file.write_text("{ malformed")

        loader = TemplateLoader(template_dir=temp_template_dir)
        # Should raise error due to invalid template
        with pytest.raises(TemplateLoadError):
            loader.load_all()

    def test_load_with_skip_invalid_option(
        self,
        temp_template_dir: Path,
        valid_template_yaml: dict[str, Any],
    ) -> None:
        """Test loading with skip_invalid option (future feature)."""
        # This tests future enhancement where we can skip invalid templates
        # Currently all templates must be valid
        pass


class TestTemplateLoaderSorting:
    """Test template sorting by priority."""

    def test_templates_sorted_by_priority(
        self,
        temp_template_dir: Path,
        valid_template_yaml: dict[str, Any],
    ) -> None:
        """Test that templates are sorted by priority (descending)."""
        templates_data = [
            ("template_a", 50),
            ("template_b", 90),
            ("template_c", 70),
            ("template_d", 85),
        ]
        for name, priority in templates_data:
            template_data = valid_template_yaml.copy()
            template_data["name"] = name
            template_data["priority"] = priority
            template_file = temp_template_dir / f"{name}.yaml"
            with template_file.open("w") as f:
                yaml.dump(template_data, f)

        loader = TemplateLoader(template_dir=temp_template_dir)
        templates = loader.load_all()

        # Should be sorted: 90, 85, 70, 50
        assert len(templates) == 4
        assert templates[0].priority == 90
        assert templates[1].priority == 85
        assert templates[2].priority == 70
        assert templates[3].priority == 50


class TestTemplateLoaderCaching:
    """Test template caching behavior (future feature)."""

    def test_reload_templates(
        self,
        temp_template_dir: Path,
        valid_template_yaml: dict[str, Any],
    ) -> None:
        """Test reloading templates after modification."""
        loader = TemplateLoader(template_dir=temp_template_dir)

        # Initial load - empty
        templates = loader.load_all()
        assert len(templates) == 0

        # Add template
        template_file = temp_template_dir / "new.yaml"
        with template_file.open("w") as f:
            yaml.dump(valid_template_yaml, f)

        # Reload
        templates = loader.load_all()
        assert len(templates) == 1


class TestTemplateLoaderIntegration:
    """Test integration with QueryTemplate model."""

    def test_loaded_template_generates_sql(
        self,
        temp_template_dir: Path,
        valid_template_yaml: dict[str, Any],
    ) -> None:
        """Test that loaded template can generate SQL."""
        template_file = temp_template_dir / "select_all.yaml"
        with template_file.open("w") as f:
            yaml.dump(valid_template_yaml, f)

        loader = TemplateLoader(template_dir=temp_template_dir)
        templates = loader.load_all()

        assert len(templates) == 1
        template = templates[0]

        # Generate SQL
        sql, params = template.generate_sql({"table": "users"})
        assert "SELECT * FROM" in sql
        assert "users" in sql  # May be quoted or unquoted
        assert "LIMIT 1000" in sql
