"""Prompt builder implementation.

Builds system and user prompts for SQL generation.
"""

import structlog

from postgres_mcp.models.schema import DatabaseSchema

logger = structlog.get_logger(__name__)


class PromptBuilder:
    """Prompt builder.

    Responsible for building system and user prompts for OpenAI API.
    """

    SYSTEM_PROMPT = """你是一个专业的 PostgreSQL SQL 查询专家。

职责:
1. 根据用户的自然语言描述生成准确的 PostgreSQL SELECT 查询
2. 仅生成只读查询（SELECT），绝不生成修改数据的语句
3. 使用提供的数据库 schema 确保表名和列名正确
4. 遵循 PostgreSQL 最佳实践

约束:
- 只生成 SELECT 语句，不允许 INSERT/UPDATE/DELETE/DDL
- 所有表名和列名必须存在于提供的 schema 中
- 使用明确的列名而非 SELECT *（除非用户明确要求）
- 添加合理的 LIMIT（默认 1000）防止返回过多数据
- 复杂条件时使用括号明确优先级

输出格式:
返回 JSON 格式（严格）:
{
  "sql": "必须是单条 SELECT 语句的字符串",
  "explanation": "简短解释（字符串）",
  "assumptions": ["做出的假设列表（字符串数组）"]
}

重要:
- sql 字段必须是字符串，不允许嵌套对象或数组
- 不要输出 Markdown、代码块或其他额外内容

错误处理:
- 如果无法理解请求，在 explanation 中说明原因
- 如果请求的表/列不存在，提示用户正确的名称
"""

    def build_system_prompt(self) -> str:
        """Build system prompt.

        Returns:
            str: System prompt string
        """
        return self.SYSTEM_PROMPT

    def build_user_prompt(
        self,
        natural_language: str,
        schema: DatabaseSchema,
        examples: list[dict[str, str]] | None = None,
        max_tables: int = 10,
    ) -> str:
        """Build user prompt.

        Args:
            natural_language: Natural language query
            schema: Database schema
            examples: Few-shot example list
            max_tables: Maximum number of tables to include (token optimization)

        Returns:
            str: User prompt string
        """
        # Select relevant tables
        relevant_tables = self._select_relevant_tables(
            natural_language, schema, max_count=max_tables
        )

        # Build DDL
        ddl = self._schema_to_ddl(schema, relevant_tables)

        # Build prompt
        prompt_parts = ["# Database Schema\n", ddl]

        # Add examples (if any)
        if examples:
            prompt_parts.append("\n# Query Examples\n")
            for i, example in enumerate(examples, 1):
                prompt_parts.append(
                    f'\nExample {i}:\nNatural Language: "{example["nl"]}"\nSQL: {example["sql"]}\n'
                )

        # Add user query
        prompt_parts.append(
            f"\n# User Query\n\n"
            f"Generate PostgreSQL SELECT query for the following natural language:\n\n"
            f'"{natural_language}"\n\n'
            f"Generate accurate SQL, brief explanation, and any assumptions."
        )

        return "".join(prompt_parts)

    def build_retry_prompt(self, original_prompt: str, validation_error: str) -> str:
        """Build retry prompt (after validation failure).

        Args:
            original_prompt: Original prompt
            validation_error: Validation error message

        Returns:
            str: Enhanced prompt string
        """
        return (
            f"{original_prompt}\n\n"
            f"**IMPORTANT**: Previous SQL validation failed:\n"
            f"{validation_error}\n\n"
            f"Please regenerate ensuring ONLY SELECT statement with no modification operations."
        )

    def _schema_to_ddl(self, schema: DatabaseSchema, relevant_tables: list[str]) -> str:
        """Convert schema to DDL format.

        Args:
            schema: Database schema
            relevant_tables: List of relevant tables

        Returns:
            str: DDL-formatted schema
        """
        ddl_parts = []

        for table_name in relevant_tables:
            if table_name not in schema.tables:
                continue

            table = schema.tables[table_name]
            columns = []

            for col in table.columns:
                col_def = f"  {col.name} {col.data_type}"
                if not col.nullable:
                    col_def += " NOT NULL"
                if col.primary_key:
                    col_def += " PRIMARY KEY"
                columns.append(col_def)

            ddl = f"CREATE TABLE {table_name} (\n" + ",\n".join(columns) + "\n);"
            ddl_parts.append(ddl)

        return "\n\n".join(ddl_parts)

    def _select_relevant_tables(
        self, natural_language: str, schema: DatabaseSchema, max_count: int = 10
    ) -> list[str]:
        """Select tables relevant to the query.

        Args:
            natural_language: Natural language query
            schema: Database schema
            max_count: Maximum number of tables to return

        Returns:
            list[str]: List of relevant table names
        """
        nl_lower = natural_language.lower()
        scored_tables = []

        for table_name in schema.tables.keys():
            score = 0

            # Direct table name match
            if table_name in nl_lower:
                score += 10

            # Table name (without underscores) match
            if table_name.replace("_", " ") in nl_lower:
                score += 8

            # Partial word match
            for word in table_name.split("_"):
                if word in nl_lower:
                    score += 2

            # Check column name match
            table = schema.tables[table_name]
            for col in table.columns:
                if col.name in nl_lower:
                    score += 3

            scored_tables.append((score, table_name))

        # Sort and return top N
        scored_tables.sort(reverse=True, key=lambda x: x[0])
        relevant = [name for score, name in scored_tables[:max_count] if score > 0]

        # If no matches, return all tables (limited count)
        if not relevant:
            relevant = list(schema.tables.keys())[:max_count]

        return relevant
