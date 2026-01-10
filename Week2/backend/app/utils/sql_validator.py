"""SQL 验证工具（使用 sqlglot）- 增强版包含多层注入防护"""

import sqlglot
from sqlglot.errors import ParseError

# 禁止的 SQL 语句类型
FORBIDDEN_STATEMENTS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "create",
    "truncate",
    "grant",
    "revoke",
    "execute",
    "call",
}

# 危险关键字列表
DANGEROUS_KEYWORDS = {
    # "UNION",  # 已移除：允许 UNION 查询
    "INTO OUTFILE",
    "INTO DUMPFILE",
    "LOAD_FILE",
    "LOAD DATA",
    "EXEC",
    "EXECUTE",
    "xp_cmdshell",  # SQL Server
    "sp_executesql",  # SQL Server
}

# 系统表前缀
SYSTEM_TABLE_PREFIXES = [
    "information_schema",
    "pg_catalog",
    "pg_",
    "mysql.",
    "sys.",
    "performance_schema",
]


def validate_sql(sql: str, dialect: str = "postgres") -> tuple[bool, str | None]:
    """
    验证 SQL 语法并检查是否为 SELECT 语句 (多层注入防护)

    Args:
        sql: SQL 查询语句
        dialect: 数据库方言 (postgres, mysql, sqlite)

    Returns:
        (is_valid, error_message)
    """
    # === 第 1 层: 注释检测 ===
    if "--" in sql or "/*" in sql or "*/" in sql or "#" in sql:
        return False, "检测到不安全的 SQL 模式: 注释。仅允许安全的 SELECT 查询。"

    # === 第 2 层: 多语句检测 ===
    # 移除末尾的分号后检查是否还有分号
    sql_stripped = sql.strip().rstrip(";").strip()
    if ";" in sql_stripped:
        return False, "检测到不安全的 SQL 模式: 多语句。仅允许单条 SELECT 查询。"

    # === 第 3 层: 危险关键字检测 ===
    sql_upper = sql.upper()
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in sql_upper:
            return False, f"检测到不安全的 SQL 模式: {keyword}。仅允许安全的 SELECT 查询。"

    # === 第 4 层: 系统表检测 ===
    sql_lower = sql.lower()
    for prefix in SYSTEM_TABLE_PREFIXES:
        # 检测完整的表名引用 (避免误判,如 my_information 表)
        if f" {prefix}" in sql_lower or f"\t{prefix}" in sql_lower or sql_lower.startswith(prefix):
            return False, f"检测到不安全的 SQL 模式: 访问系统表 {prefix}。"

    # === 第 5 层: sqlglot 语法验证 ===
    try:
        # 解析 SQL (使用 read 参数指定方言)
        parsed = sqlglot.parse(sql, read=dialect)
        if not parsed:
            return False, "无法解析 SQL"

        # 检查每个语句
        for statement in parsed:
            if statement is None:
                continue
            statement_type = statement.key.lower()

            # 检查是否为禁止的语句类型
            if statement_type in FORBIDDEN_STATEMENTS:
                return False, f"仅允许 SELECT 查询，{statement_type.upper()} 操作已被阻止"

            # 检查是否为 SELECT 或 UNION 语句
            if statement_type not in ("select", "union"):
                return False, f"仅允许 SELECT 查询，检测到 {statement_type.upper()} 语句"

        return True, None

    except ParseError as e:
        # 提取错误位置信息
        error_msg = str(e)
        if hasattr(e, "errors") and e.errors:
            first_error = e.errors[0]
            if "line" in first_error and "col" in first_error:
                line = first_error.get("line", 1)
                col = first_error.get("col", 1)
                return False, f"语法错误：{error_msg}。位置：第 {line} 行，第 {col} 列"
        return False, f"语法错误：{error_msg}"

    except Exception as e:
        return False, f"SQL 验证失败：{str(e)}"


def add_limit_if_missing(sql: str, limit: int = 1000) -> str:
    """
    智能添加 LIMIT - 聚合查询豁免

    Args:
        sql: SQL 查询语句
        limit: 默认限制行数 (最大 10000)

    Returns:
        修改后的 SQL
    """
    try:
        # 限制最大值
        if limit > 10000:
            limit = 10000

        # 解析 SQL
        parsed = sqlglot.parse_one(sql)
        if not parsed or parsed.key.lower() != "select":
            return sql

        # 检查是否已有 LIMIT
        existing_limit = parsed.args.get("limit")
        if existing_limit:
            # 检查是否超过最大值
            try:
                limit_value = int(str(existing_limit.expression))
                if limit_value > 10000:
                    # 替换为最大值
                    parsed = parsed.limit(10000, copy=False)
                    return parsed.sql()
            except (AttributeError, ValueError):
                pass
            return sql

        # === 检测聚合查询豁免 ===
        has_aggregation = _detect_aggregation(parsed)
        has_group_by = parsed.args.get("group") is not None

        # 聚合查询且无 GROUP BY 则豁免 LIMIT
        if has_aggregation and not has_group_by:
            return sql

        # 添加 LIMIT (使用 limit() 方法)
        parsed = parsed.limit(limit)
        return parsed.sql()

    except Exception:
        # 如果解析失败，简单地在末尾添加 LIMIT
        sql_upper = sql.upper().strip()

        # 检查是否有 LIMIT
        if "LIMIT" in sql_upper:
            return sql

        # 简单的聚合检测
        if _simple_aggregation_check(sql_upper):
            return sql

        # 移除末尾的分号（如果有）
        sql_clean = sql.rstrip().rstrip(";")
        return f"{sql_clean} LIMIT {limit}"


def _detect_aggregation(statement: sqlglot.exp.Expression) -> bool:
    """
    检测是否包含聚合函数

    Args:
        statement: sqlglot 解析的 SQL 语句

    Returns:
        是否包含聚合函数
    """
    AGG_FUNCTIONS = {"COUNT", "SUM", "AVG", "MAX", "MIN"}

    # 遍历所有节点查找聚合函数
    for node in statement.walk():
        if isinstance(node, sqlglot.exp.AggFunc):
            return True
        # 检查函数名
        if isinstance(node, sqlglot.exp.Func):
            if node.name and node.name.upper() in AGG_FUNCTIONS:
                return True

    return False


def _simple_aggregation_check(sql_upper: str) -> bool:
    """
    简单的聚合函数检测 (备用方法)

    Args:
        sql_upper: 大写的 SQL 语句

    Returns:
        是否可能包含聚合函数
    """
    AGG_KEYWORDS = ["COUNT(", "SUM(", "AVG(", "MAX(", "MIN("]
    return any(keyword in sql_upper for keyword in AGG_KEYWORDS) and "GROUP BY" not in sql_upper
