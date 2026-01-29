"""Response parser implementation.

Parses OpenAI API responses.
"""

import json
from dataclasses import dataclass

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ParsedResponse:
    """Parsed response."""

    sql: str
    explanation: str
    assumptions: list[str]


class ResponseParser:
    """Response parser.

    Parses JSON responses from OpenAI API.
    """

    def parse(self, content: str) -> ParsedResponse:
        """Parse response content.

        Args:
            content: Content returned by OpenAI

        Returns:
            ParsedResponse: Parsed response object

        Raises:
            ValueError: If parsing fails
        """
        try:
            data = json.loads(content)

            return ParsedResponse(
                sql=data.get("sql", "").strip(),
                explanation=data.get("explanation", "").strip(),
                assumptions=data.get("assumptions", []),
            )
        except json.JSONDecodeError as e:
            logger.error("parse_failed", content=content[:200], error=str(e))
            raise ValueError(f"Failed to parse JSON response: {e}") from e
        except Exception as e:
            logger.error("unexpected_parse_error", error=str(e))
            raise ValueError(f"Error parsing response: {e}") from e
