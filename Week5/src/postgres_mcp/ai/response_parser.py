"""Response Parser 实现。

解析 OpenAI API 的响应。
"""

import json
from dataclasses import dataclass

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class ParsedResponse:
    """解析后的响应。"""

    sql: str
    explanation: str
    assumptions: list[str]


class ResponseParser:
    """响应解析器。

    解析 OpenAI API 返回的 JSON 响应。
    """

    def parse(self, content: str) -> ParsedResponse:
        """解析响应内容。

        Args:
            content: OpenAI 返回的内容

        Returns:
            ParsedResponse: 解析后的响应

        Raises:
            ValueError: 解析失败
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
            raise ValueError(f"无法解析 JSON 响应: {e}") from e
        except Exception as e:
            logger.error("unexpected_parse_error", error=str(e))
            raise ValueError(f"解析响应时出错: {e}") from e
