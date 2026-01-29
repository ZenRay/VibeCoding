"""
Template matcher for matching natural language queries to SQL templates.

This module provides functionality to match user queries against a library of
predefined templates using keyword matching, regex patterns, and entity extraction.
"""

from __future__ import annotations

import re
from typing import TypedDict

import structlog

from postgres_mcp.models.schema import TableSchema
from postgres_mcp.models.template import QueryTemplate

logger = structlog.get_logger(__name__)


class MatchResult(TypedDict):
    """Result of template matching."""

    template: QueryTemplate
    score: float
    keyword_matches: int
    pattern_matches: int
    priority: int
    entities: dict[str, str]


class TemplateMatcher:
    """
    Match natural language queries to SQL templates.

    Uses a four-stage scoring system:
    1. Keyword matching (case-insensitive)
    2. Regex pattern matching
    3. Template priority weighting
    4. Entity extraction from query

    Args:
    ----------
        templates: List of query templates to match against.

    Returns:
    ----------
        None

    Example:
    ----------
        >>> matcher = TemplateMatcher(templates=loaded_templates)
        >>> match = matcher.match("显示所有用户", schema)
        >>> if match:
        ...     sql, params = match["template"].generate_sql(match["entities"])
    """

    def __init__(self, templates: list[QueryTemplate]) -> None:
        """Initialize template matcher with templates."""
        self.templates = templates
        logger.info("template_matcher_initialized", template_count=len(templates))

    def match(
        self,
        query: str,
        schema: dict[str, TableSchema],
        threshold: float = 5.0,
    ) -> MatchResult | None:
        """
        Find the best matching template for a natural language query.

        Args:
        ----------
            query: Natural language query string.
            schema: Database schema for entity extraction.
            threshold: Minimum score threshold (default 5.0).

        Returns:
        ----------
            Best matching template with score and entities, or None if no match.

        Example:
        ----------
            >>> match = matcher.match("显示所有产品", schema)
            >>> if match:
            ...     print(f"Matched: {match['template'].name}")
            ...     print(f"Score: {match['score']}")
            ...     print(f"Entities: {match['entities']}")
        """
        if not query or not query.strip():
            logger.debug("empty_query_provided")
            return None

        if not self.templates:
            logger.warning("no_templates_available")
            return None

        query = query.strip()
        logger.debug("matching_query", query=query, template_count=len(self.templates))

        # Score all templates
        scored_templates = [self._score_template(query, template) for template in self.templates]

        # Filter by threshold and sort by score
        valid_matches = [match for match in scored_templates if match["score"] >= threshold]
        if not valid_matches:
            logger.debug("no_templates_above_threshold", threshold=threshold)
            return None

        valid_matches.sort(key=lambda m: m["score"], reverse=True)
        best_match = valid_matches[0]

        # Extract entities for the best match
        entities = self._extract_entities(query, schema)
        best_match["entities"] = entities

        logger.info(
            "template_matched",
            template_name=best_match["template"].name,
            score=best_match["score"],
            keyword_matches=best_match["keyword_matches"],
            pattern_matches=best_match["pattern_matches"],
            entities=entities,
        )

        return best_match

    def _score_template(self, query: str, template: QueryTemplate) -> MatchResult:
        """
        Score a template against a query.

        Scoring algorithm:
        - Keyword match: +2 points per keyword
        - Pattern match: +3 points per pattern
        - Priority weight: priority / 10 (0-10 points)

        Args:
        ----------
            query: Natural language query.
            template: Template to score.

        Returns:
        ----------
            Scored template match result.
        """
        query_lower = query.lower()

        # Keyword matching (case-insensitive)
        keyword_matches = self._match_keywords(query_lower, template)

        # Pattern matching
        pattern_matches = self._match_patterns(query, template)

        # Calculate score
        score = (
            keyword_matches * 2.0  # Keyword weight
            + pattern_matches * 3.0  # Pattern weight
            + template.priority / 10.0  # Priority weight (0-10)
        )

        return MatchResult(
            template=template,
            score=score,
            keyword_matches=keyword_matches,
            pattern_matches=pattern_matches,
            priority=template.priority,
            entities={},  # Populated later for best match
        )

    def _match_keywords(self, query_lower: str, template: QueryTemplate) -> int:
        """
        Count keyword matches in query (case-insensitive).

        Args:
        ----------
            query_lower: Lowercase query string.
            template: Template to match keywords from.

        Returns:
        ----------
            Number of keyword matches.
        """
        matches = 0
        for keyword in template.keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in query_lower:
                matches += 1
                logger.debug("keyword_matched", keyword=keyword, query=query_lower)

        return matches

    def _match_patterns(self, query: str, template: QueryTemplate) -> int:
        """
        Count regex pattern matches in query.

        Args:
        ----------
            query: Query string.
            template: Template to match patterns from.

        Returns:
        ----------
            Number of pattern matches.
        """
        matches = 0
        for pattern in template.patterns:
            try:
                if re.search(pattern, query, re.IGNORECASE):
                    matches += 1
                    logger.debug("pattern_matched", pattern=pattern, query=query)
            except re.error as e:
                logger.warning("invalid_regex_pattern", pattern=pattern, error=str(e))

        return matches

    def _extract_entities(
        self,
        query: str,
        schema: dict[str, TableSchema],
    ) -> dict[str, str]:
        """
        Extract entities (table names, column names) from query.

        Uses schema to identify valid table and column names in the query.

        Args:
        ----------
            query: Natural language query.
            schema: Database schema.

        Returns:
        ----------
            Dictionary of extracted entities (e.g., {"table": "users"}).
        """
        entities: dict[str, str] = {}

        if not schema:
            logger.debug("empty_schema_no_entity_extraction")
            return entities

        query_lower = query.lower()

        # Extract table names
        # Try to find table names in query (exact match or Chinese mapping)
        for table_name in schema.keys():
            # Direct table name match
            if table_name.lower() in query_lower:
                entities["table"] = table_name
                logger.debug("entity_extracted_table", table=table_name, query=query)
                break

            # Try common Chinese mappings (extendable)
            chinese_mappings = {
                "users": ["用户", "使用者"],
                "products": ["产品", "商品"],
                "orders": ["订单", "订购"],
                "customers": ["客户", "顾客"],
                "employees": ["员工", "雇员"],
                "categories": ["类别", "分类"],
                "reviews": ["评论", "评价"],
                "payments": ["支付", "付款"],
                "shipments": ["发货", "物流"],
                "invoices": ["发票", "账单"],
            }

            # Check if any Chinese term maps to this table
            chinese_terms = chinese_mappings.get(table_name, [])
            for term in chinese_terms:
                if term in query:
                    entities["table"] = table_name
                    logger.debug(
                        "entity_extracted_table_chinese",
                        table=table_name,
                        chinese_term=term,
                        query=query,
                    )
                    break

            if "table" in entities:
                break

        # Extract column names (if table is known)
        if "table" in entities:
            table = schema[entities["table"]]
            for column in table.columns:
                if column.name.lower() in query_lower:
                    entities["column"] = column.name
                    logger.debug("entity_extracted_column", column=column.name, query=query)
                    # Only extract first column for now
                    break

        return entities

    def match_all(
        self,
        query: str,
        schema: dict[str, TableSchema],
        threshold: float = 5.0,
        top_k: int = 3,
    ) -> list[MatchResult]:
        """
        Find all matching templates above threshold.

        Args:
        ----------
            query: Natural language query string.
            schema: Database schema for entity extraction.
            threshold: Minimum score threshold (default 5.0).
            top_k: Maximum number of matches to return (default 3).

        Returns:
        ----------
            List of top-k matching templates with scores and entities.

        Example:
        ----------
            >>> matches = matcher.match_all("显示用户", schema, top_k=5)
            >>> for match in matches:
            ...     print(f"{match['template'].name}: {match['score']}")
        """
        if not query or not query.strip():
            return []

        if not self.templates:
            return []

        query = query.strip()

        # Score all templates
        scored_templates = [self._score_template(query, template) for template in self.templates]

        # Filter by threshold and sort
        valid_matches = [match for match in scored_templates if match["score"] >= threshold]
        valid_matches.sort(key=lambda m: m["score"], reverse=True)

        # Take top k
        top_matches = valid_matches[:top_k]

        # Extract entities for all top matches
        entities = self._extract_entities(query, schema)
        for match in top_matches:
            match["entities"] = entities.copy()

        logger.info(
            "multiple_templates_matched",
            query=query,
            match_count=len(top_matches),
            top_score=top_matches[0]["score"] if top_matches else 0,
        )

        return top_matches
