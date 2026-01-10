"""SQL 验证工具测试 - 包含注入防护测试"""

from app.utils.sql_validator import add_limit_if_missing, validate_sql


def test_validate_select():
    """测试有效的 SELECT 语句"""
    is_valid, error = validate_sql("SELECT * FROM users", "postgres")
    assert is_valid is True
    assert error is None


def test_validate_insert():
    """测试禁止的 INSERT 语句"""
    is_valid, error = validate_sql("INSERT INTO users VALUES (1)", "postgres")
    assert is_valid is False
    assert "INSERT" in error or "仅允许 SELECT" in error


def test_add_limit():
    """测试添加 LIMIT"""
    sql = "SELECT * FROM users"
    result = add_limit_if_missing(sql, limit=100)
    assert "LIMIT" in result.upper()


def test_add_limit_already_exists():
    """测试已有 LIMIT 的情况"""
    sql = "SELECT * FROM users LIMIT 10"
    result = add_limit_if_missing(sql, limit=100)
    assert result == sql  # 不应重复添加


# ========== 注入防护测试 ==========


def test_sql_injection_comment_double_dash():
    """测试注释注入 - 双横线"""
    is_valid, error = validate_sql("SELECT * FROM users -- WHERE role='admin'", "postgres")
    assert is_valid is False
    assert "注释" in error


def test_sql_injection_comment_hash():
    """测试注释注入 - 井号"""
    is_valid, error = validate_sql("SELECT * FROM users # comment", "postgres")
    assert is_valid is False
    assert "注释" in error


def test_sql_injection_comment_multiline():
    """测试注释注入 - 多行注释"""
    is_valid, error = validate_sql("SELECT * FROM users /* comment */ WHERE id=1", "postgres")
    assert is_valid is False
    assert "注释" in error


def test_sql_injection_multiple_statements():
    """测试多语句注入"""
    is_valid, error = validate_sql("SELECT * FROM users; DROP TABLE users", "postgres")
    assert is_valid is False
    assert "多语句" in error


def test_sql_injection_union():
    """测试 UNION 注入"""
    is_valid, error = validate_sql("SELECT * FROM users UNION SELECT * FROM passwords", "postgres")
    assert is_valid is False
    assert "UNION" in error


def test_sql_injection_into_outfile():
    """测试 INTO OUTFILE 注入"""
    is_valid, error = validate_sql("SELECT * FROM users INTO OUTFILE '/tmp/users.txt'", "postgres")
    assert is_valid is False
    assert "INTO OUTFILE" in error


def test_sql_injection_system_table_information_schema():
    """测试系统表访问 - information_schema"""
    is_valid, error = validate_sql("SELECT * FROM information_schema.tables", "postgres")
    assert is_valid is False
    assert "系统表" in error or "information_schema" in error


def test_sql_injection_system_table_pg_catalog():
    """测试系统表访问 - pg_catalog"""
    is_valid, error = validate_sql("SELECT * FROM pg_catalog.pg_tables", "postgres")
    assert is_valid is False
    assert "系统表" in error or "pg_" in error


def test_sql_injection_system_table_mysql():
    """测试系统表访问 - mysql"""
    is_valid, error = validate_sql("SELECT * FROM mysql.user", "mysql")
    assert is_valid is False
    assert "系统表" in error or "mysql" in error


def test_valid_select_with_where():
    """测试正常的 SELECT 语句 - 带 WHERE"""
    is_valid, error = validate_sql("SELECT id, name FROM users WHERE age > 18", "postgres")
    assert is_valid is True
    assert error is None


def test_valid_select_with_join():
    """测试正常的 SELECT 语句 - 带 JOIN"""
    is_valid, error = validate_sql(
        "SELECT u.name, o.total FROM users u JOIN orders o ON u.id = o.user_id", "postgres"
    )
    assert is_valid is True
    assert error is None


def test_valid_select_with_aggregation():
    """测试正常的 SELECT 语句 - 带聚合函数"""
    is_valid, error = validate_sql("SELECT COUNT(*), AVG(age) FROM users GROUP BY city", "postgres")
    assert is_valid is True
    assert error is None


# ========== 智能 LIMIT 测试 ==========


def test_aggregation_no_limit_added():
    """测试聚合查询不添加 LIMIT"""
    sql = "SELECT COUNT(*) FROM users"
    result = add_limit_if_missing(sql, limit=1000)
    assert "LIMIT" not in result.upper()


def test_aggregation_with_sum():
    """测试 SUM 聚合查询不添加 LIMIT"""
    sql = "SELECT SUM(amount) FROM orders"
    result = add_limit_if_missing(sql, limit=1000)
    assert "LIMIT" not in result.upper()


def test_aggregation_with_group_by_adds_limit():
    """测试带 GROUP BY 的聚合查询添加 LIMIT"""
    sql = "SELECT city, COUNT(*) FROM users GROUP BY city"
    result = add_limit_if_missing(sql, limit=1000)
    assert "LIMIT" in result.upper()


def test_limit_exceeds_max():
    """测试超过最大值的 LIMIT 被限制为 10000"""
    sql = "SELECT * FROM users LIMIT 50000"
    result = add_limit_if_missing(sql, limit=1000)
    assert "LIMIT 10000" in result or "LIMIT  10000" in result


def test_normal_select_adds_limit():
    """测试普通 SELECT 添加 LIMIT"""
    sql = "SELECT * FROM users WHERE age > 18"
    result = add_limit_if_missing(sql, limit=500)
    assert "LIMIT" in result.upper()
    assert "500" in result or "LIMIT 500" in result
