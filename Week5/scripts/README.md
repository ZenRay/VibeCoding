# Week5 测试脚本

本目录包含 PostgreSQL MCP Server 的生产测试脚本。

## 📝 测试脚本

### 1. test_production.py
**完整的生产功能测试**

测试范围:
- ✅ 配置加载
- ✅ 数据库连接 (3个测试数据库)
- ✅ 数据库统计信息
- ✅ SQL 安全验证 (8项测试)
- ✅ 直接查询执行 (8个查询)

运行:
```bash
cd /home/ray/Documents/VibeCoding/Week5
source .venv/bin/activate
python scripts/test_production.py
```

输出: `test_results_production.json`

### 2. test_ai_generation.py
**AI SQL 生成测试框架**

测试范围:
- ✅ AI 客户端初始化 (通义千问)
- ✅ Schema 检查
- ✅ SQL 生成验证
- ⏳ 需要完整的 SQLGenerator 集成

运行:
```bash
cd /home/ray/Documents/VibeCoding/Week5
source .venv/bin/activate
python scripts/test_ai_generation.py
```

输出: `test_results_ai_generation.json`

### 3. test_production_full.py
**完整端到端测试** (实验性)

包含:
- 数据库连接测试
- AI SQL 生成测试
- 查询执行测试

注意: 需要完整的依赖和配置

## 🔧 前置要求

### 1. 数据库
启动测试数据库:
```bash
cd fixtures
docker compose up -d
```

### 2. 环境变量
```bash
export TEST_DB_PASSWORD="testpass123"
export OPENAI_API_KEY="your-api-key"  # 如果未在 config.yaml 中配置
```

### 3. 配置文件
确保 `config/config.yaml` 已配置:
```yaml
databases:
  - name: "ecommerce_small"
    host: "localhost"
    port: 5432
    # ...

openai:
  api_key: "sk-your-key"  # 或使用 api_key_env_var
  model: "qwen-turbo-latest"
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
```

## 📊 测试结果

测试结果会生成 JSON 文件,包含:
- 测试通过/失败统计
- 详细错误信息
- 性能数据
- 数据库统计

**注意**: JSON 结果文件在 `.gitignore` 中,不会被提交。

## 📚 相关文档

详细测试报告和文档位于:
```
specs/001-postgres-mcp/testing/
├── PRODUCTION_TEST_REPORT_FULL.md  # 完整测试报告
├── PRODUCTION_TEST_REPORT.md       # 基础测试报告  
└── README_DASHSCOPE.md             # 阿里百炼使用说明
```

## 🚀 快速测试

运行基础生产测试:
```bash
cd /home/ray/Documents/VibeCoding/Week5
source .venv/bin/activate

# 1. 启动测试数据库
cd fixtures && docker compose up -d && cd ..

# 2. 设置环境变量
export TEST_DB_PASSWORD="testpass123"

# 3. 运行测试
python scripts/test_production.py
```

预期结果: `22/22 tests passed (100%)`
