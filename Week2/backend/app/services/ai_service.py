"""AI 服务（OpenAI SQL 生成）- 增强版包含安全验证和审计"""

import logging
import re
from datetime import UTC, datetime

import sqlglot
from openai import AsyncOpenAI

from app.config import settings
from app.models.metadata import DatabaseMetadata
from app.utils.error_handler import ErrorCode, create_error_response

logger = logging.getLogger(__name__)

# 白名单关键字
ALLOWED_KEYWORDS = {
    "SELECT",
    "FROM",
    "WHERE",
    "JOIN",
    "INNER",
    "LEFT",
    "RIGHT",
    "OUTER",
    "ON",
    "AND",
    "OR",
    "NOT",
    "IN",
    "LIKE",
    "BETWEEN",
    "IS",
    "NULL",
    "GROUP",
    "BY",
    "HAVING",
    "ORDER",
    "ASC",
    "DESC",
    "LIMIT",
    "OFFSET",
    "AS",
    "DISTINCT",
    "COUNT",
    "SUM",
    "AVG",
    "MAX",
    "MIN",
    "CASE",
    "WHEN",
    "THEN",
    "ELSE",
    "END",
}

# 禁止的系统函数
FORBIDDEN_FUNCTIONS = [
    "VERSION",
    "CURRENT_USER",
    "USER",
    "DATABASE",
    "SCHEMA",
    "SLEEP",
    "BENCHMARK",
    "LOAD_FILE",
    "INTO",
    "OUTFILE",
    "DUMPFILE",
]

# 系统表前缀
SYSTEM_TABLE_PREFIXES = [
    "information_schema",
    "pg_catalog",
    "pg_",
    "mysql.",
    "sys.",
    "performance_schema",
]


def format_metadata_context(metadata: DatabaseMetadata, max_tokens: int = 4000) -> str:
    """
    格式化元数据为 AI 上下文

    Args:
        metadata: 数据库元数据
        max_tokens: 最大 token 数（约 16000 字符）

    Returns:
        格式化的元数据字符串
    """
    context_parts = []

    # 添加表信息
    if metadata.tables:
        context_parts.append("表 (Tables):")
        for table in metadata.tables[:20]:  # 限制表数量
            columns = ", ".join([col.name for col in table.columns[:10]])  # 限制列数量
            context_parts.append(f"  - {table.name}: {columns}")

    # 添加视图信息
    if metadata.views:
        context_parts.append("\n视图 (Views):")
        for view in metadata.views[:10]:  # 限制视图数量
            columns = ", ".join([col.name for col in view.columns[:10]])
            context_parts.append(f"  - {view.name}: {columns}")

    context = "\n".join(context_parts)

    # 简单检查长度（实际应该使用 tiktoken 计算 tokens）
    if len(context) > max_tokens * 4:  # 粗略估算：1 token ≈ 4 字符
        context = context[: max_tokens * 4] + "\n... (部分表未包含在上下文中)"

    return context


def _clean_ai_output(sql: str) -> str:
    """
    清洗 AI 输出

    Args:
        sql: AI 生成的 SQL

    Returns:
        清洗后的 SQL
    """
    # 移除注释
    sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    sql = re.sub(r"#.*$", "", sql, flags=re.MULTILINE)

    # 移除多余空白
    sql = " ".join(sql.split())

    # 移除代码块标记
    if sql.startswith("```sql"):
        sql = sql[6:]
    if sql.startswith("```"):
        sql = sql[3:]
    if sql.endswith("```"):
        sql = sql[:-3]

    return sql.strip()


def _validate_whitelist(sql: str) -> tuple[bool, str | None]:
    """
    白名单验证

    Args:
        sql: SQL 语句

    Returns:
        (is_valid, error_message)
    """
    try:
        # 解析 SQL
        parsed = sqlglot.parse_one(sql)
        sql_upper = sql.upper()

        # 提取所有 SQL 关键字（简化版）
        keywords = set()
        for token in sql_upper.split():
            # 清理标点符号
            cleaned = re.sub(r"[^\w]", "", token)
            if cleaned and cleaned.isupper():
                keywords.add(cleaned)

        # 检测非法关键字
        illegal = (
            keywords
            - ALLOWED_KEYWORDS
            - {
                "TABLE",
                "COLUMN",
                "VALUE",
            }
        )  # 允许一些常见词
        if illegal:
            # 过滤掉表名和列名（通常不是全大写）
            real_illegal = {kw for kw in illegal if len(kw) > 2}
            if real_illegal:
                return False, f"包含非法关键字: {', '.join(list(real_illegal)[:3])}"

        # 检测子查询
        if "(" in sql and sql.count("SELECT") > 1:
            return False, "不允许子查询"

        # 检测系统函数
        for func in FORBIDDEN_FUNCTIONS:
            if func + "(" in sql_upper or func + " " in sql_upper:
                return False, f"不允许系统函数: {func}"

        return True, None

    except Exception as e:
        return False, f"验证失败: {str(e)}"


def _validate_table_names(sql: str, metadata: DatabaseMetadata) -> tuple[bool, str | None]:
    """
    验证表名存在性

    Args:
        sql: SQL 语句
        metadata: 数据库元数据

    Returns:
        (is_valid, error_message)
    """
    try:
        # 获取所有有效的表名
        valid_tables = {table.name.lower() for table in metadata.tables}
        valid_tables.update({view.name.lower() for view in metadata.views})

        # 解析 SQL 获取引用的表
        parsed = sqlglot.parse_one(sql)
        referenced_tables = set()

        for table_node in parsed.find_all(sqlglot.exp.Table):
            table_name = table_node.name.lower()
            referenced_tables.add(table_name)

        # 检查系统表
        sql_lower = sql.lower()
        for prefix in SYSTEM_TABLE_PREFIXES:
            if prefix in sql_lower:
                return False, f"不允许访问系统表: {prefix}"

        # 检查表名是否存在
        for table in referenced_tables:
            if table not in valid_tables:
                return False, f"表 '{table}' 不存在于当前数据库"

        return True, None

    except Exception as e:
        return False, f"表名验证失败: {str(e)}"


async def _log_rejected_sql(prompt: str, sql: str, reason: str):
    """
    审计日志 - 记录被拒绝的 SQL

    Args:
        prompt: 原始自然语言输入
        sql: 生成的 SQL
        reason: 拒绝原因
    """
    logger.warning(
        "AI generated SQL rejected",
        extra={
            "prompt": prompt,
            "generated_sql": sql,
            "rejection_reason": reason,
            "timestamp": datetime.now(UTC).isoformat(),
        },
    )


async def generate_sql(
    prompt: str,
    metadata: DatabaseMetadata,
    dialect: str = "postgresql",
) -> str:
    """
    使用 OpenAI 生成 SQL (含安全增强)

    Args:
        prompt: 自然语言查询描述
        metadata: 数据库元数据
        dialect: 数据库方言

    Returns:
        生成的 SQL 语句
    """
    if not settings.openai_api_key:
        raise create_error_response(
            ErrorCode.AI_SERVICE_UNAVAILABLE,
            "AI 服务未配置，请设置 OPENAI_API_KEY 环境变量",
        )

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # 格式化元数据上下文
    metadata_context = format_metadata_context(metadata)

    system_prompt = f"""你是一个 SQL 专家。根据用户的自然语言描述生成 {dialect} SQL 查询。

数据库结构:
{metadata_context}

规则:
1. 只生成 SELECT 语句
2. 不要包含 LIMIT 子句（系统会自动添加）
3. 使用正确的表名和列名
4. 只返回 SQL 语句，不要解释
5. 不要使用子查询
6. 不要使用系统函数 (VERSION, CURRENT_USER 等)
7. 如果用户描述不清晰，返回 "无法理解查询需求"
"""

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=500,
        )

        content = response.choices[0].message.content
        if not content:
            raise ValueError("AI 返回的 SQL 为空")

        # === 第 1 步: 清洗输出 ===
        cleaned_sql = _clean_ai_output(content)

        # === 第 2 步: 白名单验证 ===
        is_safe, whitelist_error = _validate_whitelist(cleaned_sql)
        if not is_safe:
            await _log_rejected_sql(prompt, cleaned_sql, f"白名单验证失败: {whitelist_error}")
            raise create_error_response(
                ErrorCode.AI_INVALID_RESPONSE,
                f"AI 生成的 SQL 包含不安全模式: {whitelist_error}。请尝试重新描述您的查询需求,或使用手动 SQL。",
            )

        # === 第 3 步: 表名验证 ===
        is_valid_tables, table_error = _validate_table_names(cleaned_sql, metadata)
        if not is_valid_tables:
            await _log_rejected_sql(prompt, cleaned_sql, f"表名验证失败: {table_error}")
            raise create_error_response(
                ErrorCode.AI_INVALID_RESPONSE,
                f"AI 生成的查询不符合安全要求: {table_error}。建议: 简化您的描述或使用手动 SQL。",
            )

        # === 第 4 步: 审计日志 (成功) ===
        logger.info(
            "AI generated SQL accepted",
            extra={
                "prompt": prompt,
                "generated_sql": cleaned_sql,
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )

        return cleaned_sql

    except Exception as e:
        # 如果是我们自己抛出的错误，直接传递
        if hasattr(e, "detail"):
            raise

        error_msg = str(e).lower()
        if "quota" in error_msg or "rate limit" in error_msg:
            raise create_error_response(
                ErrorCode.AI_QUOTA_EXCEEDED,
                "API 配额已用尽，请稍后重试",
            )
        elif "network" in error_msg or "timeout" in error_msg:
            raise create_error_response(
                ErrorCode.AI_SERVICE_UNAVAILABLE,
                "AI 服务不可用，请稍后重试或使用手动 SQL 查询",
            )
        else:
            raise create_error_response(
                ErrorCode.AI_INVALID_RESPONSE,
                f"AI 服务错误: {str(e)}",
            )
