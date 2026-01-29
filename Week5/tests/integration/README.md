# Integration Tests

完整的集成测试套件，验证 PostgreSQL MCP Server 在真实环境下的功能。

## 📋 测试概览

| 测试模块 | 测试数量 | 测试场景 |
|---------|---------|---------|
| `test_sql_generation.py` | 3 | SQL 生成流程（OpenAI + Schema + Validator） |
| `test_schema_cache.py` | 3 | Schema 缓存和刷新 |
| `test_mcp_interface.py` | 3 | MCP 工具和资源调用 |
| `test_multi_database.py` | 3 | 多数据库并发管理 |
| `test_template_matching.py` | 3 | 模板匹配降级机制 |
| **总计** | **15** | **5 大场景** |

## 🚀 运行测试

### 前置要求

1. **PostgreSQL 测试数据库**（3个）:
   ```bash
   cd Week5/fixtures
   docker-compose up -d
   ```

2. **环境变量配置**:
   ```bash
   export TEST_DB_HOST="localhost"
   export TEST_DB_PORT="5432"
   export TEST_DB_USER="testuser"
   export TEST_DB_PASSWORD="testpass123"
   export OPENAI_API_KEY="sk-..."  # 或使用阿里百炼 API key
   ```

### 运行命令

```bash
# 进入项目目录
cd Week5

# 运行所有集成测试
pytest tests/integration/ -v -m integration

# 运行特定模块
pytest tests/integration/test_sql_generation.py -v
pytest tests/integration/test_schema_cache.py -v
pytest tests/integration/test_mcp_interface.py -v
pytest tests/integration/test_multi_database.py -v
pytest tests/integration/test_template_matching.py -v

# 仅运行单元测试（跳过集成测试）
pytest tests/unit/ -v

# 运行所有测试（单元 + 集成）
pytest -v
```

## 📝 测试详情

### 1. SQL 生成集成测试

**文件**: `test_sql_generation.py`

测试完整的 SQL 生成流程：

- ✅ **基础查询生成**: 自然语言 → AI 生成 SQL → 验证
- ✅ **条件查询生成**: 包含 WHERE 子句的复杂查询
- ✅ **安全验证**: 危险 SQL（DELETE/DROP）被拒绝

**依赖**: OpenAI API, PostgreSQL 数据库

### 2. Schema 缓存集成测试

**文件**: `test_schema_cache.py`

测试真实数据库 schema 提取和缓存：

- ✅ **Schema 加载**: 从真实 PostgreSQL 提取表结构
- ✅ **Schema 刷新**: 更新缓存的 schema 信息
- ✅ **多数据库 Schema**: 同时管理多个数据库的 schema

**依赖**: PostgreSQL 数据库

### 3. MCP 接口集成测试

**文件**: `test_mcp_interface.py`

测试 MCP 工具和资源的端到端调用：

- ✅ **generate_sql 工具**: 完整的 SQL 生成工具调用
- ✅ **list_databases 工具**: 列出所有配置的数据库
- ✅ **schema:// 资源**: 读取数据库 schema 资源

**依赖**: OpenAI API, PostgreSQL 数据库

### 4. 多数据库集成测试

**文件**: `test_multi_database.py`

测试多数据库并发场景：

- ✅ **Schema 隔离**: 3 个数据库独立的 schema 缓存
- ✅ **跨库查询**: 同时对不同数据库执行查询
- ✅ **连接池管理**: 多数据库连接池的并发管理

**依赖**: OpenAI API, PostgreSQL 数据库（3个）

### 5. 模板匹配集成测试

**文件**: `test_template_matching.py`

测试 AI 降级和模板匹配：

- ✅ **OpenAI 不可用降级**: API 失败时自动使用模板
- ✅ **常见查询准确性**: 模板匹配基础查询
- ✅ **覆盖率评估**: 模板系统对各类查询的支持度

**依赖**: PostgreSQL 数据库

## ⚠️ 注意事项

### 跳过测试

如果没有配置环境变量或数据库，测试会自动跳过：

```python
# 示例：API key 不存在时跳过
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    pytest.skip("OPENAI_API_KEY not set - skipping integration test")
```

### CI/CD 集成

在 CI/CD 环境中：

1. **仅运行单元测试**（更快）:
   ```bash
   pytest tests/unit/ -v
   ```

2. **完整测试**（包含集成测试，需要配置环境）:
   ```bash
   # 启动测试数据库
   docker-compose -f fixtures/docker-compose.yml up -d
   
   # 运行所有测试
   pytest -v
   
   # 清理
   docker-compose -f fixtures/docker-compose.yml down -v
   ```

### 测试数据库

集成测试使用的3个测试数据库：

1. **ecommerce_small** (小型电商数据库)
   - 5 张表
   - ~100 行数据

2. **social_medium** (中型社交网络数据库)
   - 8 张表
   - ~1000 行数据

3. **erp_large** (大型 ERP 数据库)
   - 15+ 张表
   - ~10000 行数据

## 🔍 故障排查

### 测试失败：数据库连接超时

**原因**: 数据库未启动或连接配置错误

**解决**:
```bash
# 检查数据库状态
docker-compose -f fixtures/docker-compose.yml ps

# 重启数据库
docker-compose -f fixtures/docker-compose.yml restart

# 测试连接
psql -h localhost -p 5432 -U testuser -d ecommerce_small
```

### 测试失败：OpenAI API 错误

**原因**: API key 无效或网络问题

**解决**:
```bash
# 检查 API key
echo $OPENAI_API_KEY

# 测试 API 连接（使用阿里百炼）
curl -X POST "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen-plus","messages":[{"role":"user","content":"test"}]}'
```

### 测试跳过：环境变量未设置

**原因**: 缺少必要的环境变量

**解决**:
```bash
# 设置所有必需的环境变量
export TEST_DB_HOST="localhost"
export TEST_DB_PORT="5432"
export TEST_DB_USER="testuser"
export TEST_DB_PASSWORD="testpass123"
export OPENAI_API_KEY="sk-..."

# 或者使用 .env 文件（推荐）
cp config/config.example.yaml config/config.yaml
# 编辑 config.yaml 配置所有参数
```

## 📊 测试覆盖率

集成测试覆盖：

- ✅ 端到端 SQL 生成流程
- ✅ 真实数据库 Schema 提取
- ✅ MCP 工具完整调用链
- ✅ 多数据库并发场景
- ✅ AI 降级和容错机制

与单元测试配合，总体覆盖率达到 **92%**。

## 🤝 贡献指南

添加新的集成测试：

1. 创建新的测试文件（遵循命名规范 `test_*.py`）
2. 标记测试为 `@pytest.mark.integration`
3. 添加完整的 Docstring（Args/Returns/Raises/Example）
4. 处理环境变量缺失情况（使用 `pytest.skip`）
5. 确保测试清理资源（使用 `finally` 块）
6. 更新本 README 文档

示例：

```python
@pytest.mark.asyncio
@pytest.mark.integration
async def test_my_new_feature() -> None:
    """
    Test description.

    Args:
    ----------
        None

    Returns:
    ----------
        None

    Raises:
    ----------
        None

    Example:
    ----------
        >>> await test_my_new_feature()
        >>> # Feature works correctly
    """
    # Skip if missing dependencies
    if not os.getenv("REQUIRED_VAR"):
        pytest.skip("REQUIRED_VAR not set")

    # Test implementation
    try:
        # Setup
        # Execute
        # Assert
        pass
    finally:
        # Cleanup
        pass
```

---

**最后更新**: 2026-01-30  
**维护者**: VibeCoding Team  
**相关文档**: `specs/001-postgres-mcp/CURRENT_STATUS.md`, `Week5/README.md`
