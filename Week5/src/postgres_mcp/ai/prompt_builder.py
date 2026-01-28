"""Prompt 构建器实现。

构建用于 SQL 生成的系统和用户提示词。
"""

import structlog

from postgres_mcp.models.schema import DatabaseSchema

logger = structlog.get_logger(__name__)


class PromptBuilder:
    """Prompt 构建器。

    负责构建 OpenAI API 的系统和用户提示词。
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
返回 JSON 格式:
{
  "sql": "生成的 SQL 查询",
  "explanation": "简短解释",
  "assumptions": ["做出的假设列表"]
}

错误处理:
- 如果无法理解请求，在 explanation 中说明原因
- 如果请求的表/列不存在，提示用户正确的名称
"""

    def build_system_prompt(self) -> str:
        """构建系统提示词。

        Returns:
            str: 系统提示词
        """
        return self.SYSTEM_PROMPT

    def build_user_prompt(
        self,
        natural_language: str,
        schema: DatabaseSchema,
        examples: list[dict[str, str]] | None = None,
        max_tables: int = 10,
    ) -> str:
        """构建用户提示词。

        Args:
            natural_language: 自然语言查询
            schema: 数据库 schema
            examples: Few-shot 示例列表
            max_tables: 最多包含的表数量（token 优化）

        Returns:
            str: 用户提示词
        """
        # 选择相关表
        relevant_tables = self._select_relevant_tables(
            natural_language, schema, max_count=max_tables
        )

        # 构建 DDL
        ddl = self._schema_to_ddl(schema, relevant_tables)

        # 构建提示词
        prompt_parts = ["# 数据库 Schema\n", ddl]

        # 添加示例（如果有）
        if examples:
            prompt_parts.append("\n# 查询示例\n")
            for i, example in enumerate(examples, 1):
                prompt_parts.append(
                    f"\n示例 {i}:\n" f'自然语言: "{example["nl"]}"\n' f'SQL: {example["sql"]}\n'
                )

        # 添加用户查询
        prompt_parts.append(
            f"\n# 用户查询\n\n"
            f"请为以下自然语言生成 PostgreSQL SELECT 查询：\n\n"
            f'"{natural_language}"\n\n'
            f"生成准确的 SQL、简短解释和任何假设。"
        )

        return "".join(prompt_parts)

    def build_retry_prompt(self, original_prompt: str, validation_error: str) -> str:
        """构建重试提示词（验证失败后）。

        Args:
            original_prompt: 原始提示词
            validation_error: 验证错误信息

        Returns:
            str: 增强的提示词
        """
        return (
            f"{original_prompt}\n\n"
            f"**重要**: 上次生成的 SQL 验证失败:\n"
            f"{validation_error}\n\n"
            f"请重新生成，确保只生成 SELECT 语句，不包含任何修改操作。"
        )

    def _schema_to_ddl(self, schema: DatabaseSchema, relevant_tables: list[str]) -> str:
        """将 schema 转换为 DDL 格式。

        Args:
            schema: 数据库 schema
            relevant_tables: 相关表列表

        Returns:
            str: DDL 格式的 schema
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
        """选择与查询相关的表。

        Args:
            natural_language: 自然语言查询
            schema: 数据库 schema
            max_count: 最多返回的表数量

        Returns:
            list[str]: 相关表名列表
        """
        nl_lower = natural_language.lower()
        scored_tables = []

        for table_name in schema.tables.keys():
            score = 0

            # 表名直接匹配
            if table_name in nl_lower:
                score += 10

            # 表名（去下划线）匹配
            if table_name.replace("_", " ") in nl_lower:
                score += 8

            # 单词部分匹配
            for word in table_name.split("_"):
                if word in nl_lower:
                    score += 2

            # 检查列名匹配
            table = schema.tables[table_name]
            for col in table.columns:
                if col.name in nl_lower:
                    score += 3

            scored_tables.append((score, table_name))

        # 排序并返回前 N 个
        scored_tables.sort(reverse=True, key=lambda x: x[0])
        relevant = [name for score, name in scored_tables[:max_count] if score > 0]

        # 如果没有匹配，返回所有表（限制数量）
        if not relevant:
            relevant = list(schema.tables.keys())[:max_count]

        return relevant
