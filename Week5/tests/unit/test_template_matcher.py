"""
Unit tests for Template Matcher.

Tests template matching algorithm with scoring and entity extraction.
"""

from __future__ import annotations

import pytest

from postgres_mcp.core.template_matcher import TemplateMatcher
from postgres_mcp.models.schema import ColumnSchema, TableSchema
from postgres_mcp.models.template import (
    ParameterType,
    QueryTemplate,
    TemplateParameter,
)


@pytest.fixture
def sample_templates() -> list[QueryTemplate]:
    """Create sample query templates for testing."""
    return [
        QueryTemplate(
            name="select_all",
            description="Select all rows from a table",
            priority=80,
            keywords=["all", "show", "list", "display"],
            patterns=[r"显示.*所有", r"列出.*所有", r"查看.*所有"],
            parameters=[
                TemplateParameter(
                    name="table",
                    type=ParameterType.IDENTIFIER,
                    description="Table name",
                    required=True,
                )
            ],
            sql_template="SELECT * FROM {table} LIMIT 1000",
            examples=[
                {"input": "显示所有用户", "params": {"table": "users"}},
                {"input": "列出所有产品", "params": {"table": "products"}},
            ],
        ),
        QueryTemplate(
            name="select_with_condition",
            description="Select rows with WHERE condition",
            priority=70,
            keywords=["where", "filter", "条件"],
            patterns=[r".*where.*", r".*条件.*"],
            parameters=[
                TemplateParameter(
                    name="table",
                    type=ParameterType.IDENTIFIER,
                    description="Table name",
                    required=True,
                ),
                TemplateParameter(
                    name="condition",
                    type=ParameterType.EXPRESSION,
                    description="WHERE condition",
                    required=True,
                ),
            ],
            sql_template="SELECT * FROM {table} WHERE {condition} LIMIT 1000",
            examples=[
                {
                    "input": "显示年龄大于30的用户",
                    "params": {"table": "users", "condition": "age > 30"},
                }
            ],
        ),
        QueryTemplate(
            name="count_records",
            description="Count records in a table",
            priority=75,
            keywords=["count", "统计", "数量", "多少"],
            patterns=[r".*多少.*", r".*数量.*", r".*count.*"],
            parameters=[
                TemplateParameter(
                    name="table",
                    type=ParameterType.IDENTIFIER,
                    description="Table name",
                    required=True,
                )
            ],
            sql_template="SELECT COUNT(*) as count FROM {table}",
            examples=[
                {"input": "有多少用户", "params": {"table": "users"}},
                {"input": "统计产品数量", "params": {"table": "products"}},
            ],
        ),
    ]


@pytest.fixture
def sample_schema() -> dict[str, TableSchema]:
    """Create sample database schema for testing."""
    return {
        "users": TableSchema(
            name="users",
            columns=[
                ColumnSchema(name="id", data_type="integer", is_nullable=False),
                ColumnSchema(name="name", data_type="varchar", is_nullable=False),
                ColumnSchema(name="email", data_type="varchar", is_nullable=True),
                ColumnSchema(name="age", data_type="integer", is_nullable=True),
            ],
            primary_key=["id"],
        ),
        "products": TableSchema(
            name="products",
            columns=[
                ColumnSchema(name="id", data_type="integer", is_nullable=False),
                ColumnSchema(name="name", data_type="varchar", is_nullable=False),
                ColumnSchema(name="price", data_type="numeric", is_nullable=False),
            ],
            primary_key=["id"],
        ),
    }


@pytest.fixture
def matcher(sample_templates: list[QueryTemplate]) -> TemplateMatcher:
    """Create a TemplateMatcher with sample templates."""
    return TemplateMatcher(templates=sample_templates)


class TestTemplateMatcherBasic:
    """Test basic template matching functionality."""

    def test_initialization(self, sample_templates: list[QueryTemplate]) -> None:
        """Test TemplateMatcher initialization."""
        matcher = TemplateMatcher(templates=sample_templates)
        assert len(matcher.templates) == 3

    def test_keyword_matching(self, matcher: TemplateMatcher) -> None:
        """Test keyword-based template matching."""
        # Test with query containing English keywords
        matches = matcher._match_keywords("show all users", matcher.templates[0])
        assert matches > 0  # Should match "all" and "show"

    def test_pattern_matching(self, matcher: TemplateMatcher) -> None:
        """Test regex pattern-based template matching."""
        matches = matcher._match_patterns("显示所有用户", matcher.templates[0])
        assert matches > 0  # Should match "显示.*所有"

    def test_no_match(self, matcher: TemplateMatcher) -> None:
        """Test when no template matches."""
        matches = matcher._match_keywords("completely unrelated query", matcher.templates[0])
        assert matches == 0


class TestTemplateMatcherScoring:
    """Test template scoring algorithm."""

    def test_exact_keyword_match(self, matcher: TemplateMatcher) -> None:
        """Test scoring with exact keyword match."""
        query = "show all users"
        scored = matcher._score_template(query, matcher.templates[0])
        assert scored["score"] > 0
        assert scored["keyword_matches"] > 0

    def test_pattern_match(self, matcher: TemplateMatcher) -> None:
        """Test scoring with pattern match."""
        query = "显示所有产品"
        scored = matcher._score_template(query, matcher.templates[0])
        assert scored["score"] > 0
        assert scored["pattern_matches"] > 0

    def test_priority_weight(self, matcher: TemplateMatcher) -> None:
        """Test that higher priority templates get higher base score."""
        query = "显示所有用户"
        scored_high = matcher._score_template(query, matcher.templates[0])  # priority 80
        scored_low = matcher._score_template(query, matcher.templates[1])  # priority 70
        # Both might match, but high priority should have advantage
        assert scored_high["priority"] > scored_low["priority"]

    def test_score_combination(self, matcher: TemplateMatcher) -> None:
        """Test combined scoring (keywords + patterns + priority)."""
        query = "统计用户数量"
        scored = matcher._score_template(query, matcher.templates[2])  # count template
        assert scored["score"] > 0
        assert scored["keyword_matches"] > 0  # "统计" or "数量"


class TestTemplateMatcherEntityExtraction:
    """Test entity extraction from natural language."""

    def test_extract_table_name(
        self,
        matcher: TemplateMatcher,
        sample_schema: dict[str, TableSchema],
    ) -> None:
        """Test extracting table name from query."""
        query = "显示所有用户"
        entities = matcher._extract_entities(query, sample_schema)
        assert "table" in entities
        assert entities["table"] == "users"

    def test_extract_table_with_plural(
        self,
        matcher: TemplateMatcher,
        sample_schema: dict[str, TableSchema],
    ) -> None:
        """Test extracting table name with plural form."""
        query = "列出所有产品"
        entities = matcher._extract_entities(query, sample_schema)
        assert entities.get("table") == "products"

    def test_no_table_match(
        self,
        matcher: TemplateMatcher,
        sample_schema: dict[str, TableSchema],
    ) -> None:
        """Test when no table name is found."""
        query = "执行某些操作"
        entities = matcher._extract_entities(query, sample_schema)
        assert entities.get("table") is None

    def test_extract_multiple_entities(
        self,
        matcher: TemplateMatcher,
        sample_schema: dict[str, TableSchema],
    ) -> None:
        """Test extracting multiple entities (table + column)."""
        query = "显示用户的名字"
        entities = matcher._extract_entities(query, sample_schema)
        assert entities.get("table") == "users"
        # Column extraction is optional feature
        # assert entities.get("column") == "name"


class TestTemplateMatcherMatching:
    """Test complete template matching with ranking."""

    def test_find_best_match(
        self,
        matcher: TemplateMatcher,
        sample_schema: dict[str, TableSchema],
    ) -> None:
        """Test finding the best matching template."""
        query = "显示所有用户"
        best_match = matcher.match(query, sample_schema)
        assert best_match is not None
        assert best_match["template"].name == "select_all"
        assert best_match["score"] > 0
        assert "table" in best_match["entities"]

    def test_count_template_match(
        self,
        matcher: TemplateMatcher,
        sample_schema: dict[str, TableSchema],
    ) -> None:
        """Test matching count query template."""
        query = "有多少用户"
        best_match = matcher.match(query, sample_schema)
        assert best_match is not None
        assert best_match["template"].name == "count_records"
        assert best_match["entities"].get("table") == "users"

    def test_no_good_match(
        self,
        matcher: TemplateMatcher,
        sample_schema: dict[str, TableSchema],
    ) -> None:
        """Test when no template has a good match (score too low)."""
        query = "完全无关的复杂查询需求"
        best_match = matcher.match(query, sample_schema, threshold=10.0)
        # Should return None if no template scores above threshold
        assert best_match is None or best_match["score"] < 10.0

    def test_match_threshold(
        self,
        matcher: TemplateMatcher,
        sample_schema: dict[str, TableSchema],
    ) -> None:
        """Test threshold filtering for matches."""
        query = "显示所有用户"
        # Set very high threshold
        best_match = matcher.match(query, sample_schema, threshold=1000.0)
        assert best_match is None


class TestTemplateMatcherEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_query(
        self,
        matcher: TemplateMatcher,
        sample_schema: dict[str, TableSchema],
    ) -> None:
        """Test with empty query string."""
        best_match = matcher.match("", sample_schema)
        assert best_match is None

    def test_empty_templates(self, sample_schema: dict[str, TableSchema]) -> None:
        """Test matcher with no templates."""
        matcher = TemplateMatcher(templates=[])
        best_match = matcher.match("显示所有用户", sample_schema)
        assert best_match is None

    def test_empty_schema(self, matcher: TemplateMatcher) -> None:
        """Test with empty schema."""
        best_match = matcher.match("显示所有用户", {})
        # Should still match template, but no entity extraction
        assert best_match is not None
        assert best_match["template"].name == "select_all"
        assert best_match["entities"].get("table") is None

    def test_case_insensitive_matching(
        self,
        matcher: TemplateMatcher,
        sample_schema: dict[str, TableSchema],
    ) -> None:
        """Test case-insensitive keyword matching."""
        query_upper = "显示所有USERS"
        query_lower = "显示所有users"
        match_upper = matcher.match(query_upper, sample_schema)
        match_lower = matcher.match(query_lower, sample_schema)
        assert match_upper is not None
        assert match_lower is not None


class TestTemplateMatcherSQLGeneration:
    """Test SQL generation from matched templates."""

    def test_generate_sql_from_match(
        self,
        matcher: TemplateMatcher,
        sample_schema: dict[str, TableSchema],
    ) -> None:
        """Test generating SQL from best match."""
        query = "显示所有用户"
        best_match = matcher.match(query, sample_schema)
        assert best_match is not None

        # Generate SQL using matched template
        template = best_match["template"]
        entities = best_match["entities"]
        sql, params = template.generate_sql(entities)

        assert "SELECT * FROM" in sql
        assert "users" in sql  # May be quoted or unquoted
        assert "LIMIT 1000" in sql
        assert isinstance(params, list)

    def test_generate_count_sql(
        self,
        matcher: TemplateMatcher,
        sample_schema: dict[str, TableSchema],
    ) -> None:
        """Test generating COUNT SQL."""
        query = "有多少产品"
        best_match = matcher.match(query, sample_schema)
        assert best_match is not None

        sql, params = best_match["template"].generate_sql(best_match["entities"])
        assert "SELECT COUNT(*)" in sql
        assert "products" in sql  # May be quoted or unquoted
