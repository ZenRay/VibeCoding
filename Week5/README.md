# PostgreSQL MCP Server

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-113%2F122%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-90--93%25-brightgreen)](tests/)

**Natural Language to SQL Query Server powered by OpenAI GPT-4o-mini & 阿里百炼**

Query your PostgreSQL databases using natural language through the Model Context Protocol (MCP). This server automatically generates safe, validated SQL queries and executes them with comprehensive error handling.

## Features

- 🗣️ **Natural Language to SQL**: Convert plain English to PostgreSQL queries
- 🔒 **Security First**: Enforces read-only operations with AST-based validation
- 📊 **Smart Schema Caching**: Auto-discovers and caches database structures  
- ⚡ **Query Execution**: Generate SQL or execute queries and return formatted results
- 📜 **Query History**: Automatic logging and audit trail (JSONL format) ✨ **NEW**
- 🔄 **Multi-Database Support**: Connect to multiple PostgreSQL databases simultaneously
- 📈 **Result Formatting**: Automatic Markdown table formatting with row limits

## Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 12.0+
- OpenAI API key **或** 阿里百炼 API key
- UV package manager (recommended) or pip

### Installation

```bash
# Clone repository
cd ~/Documents/VibeCoding/Week5

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Or using UV (recommended)
uv pip install -e .
```

### Configuration

1. **Create configuration file** (required, contains sensitive info):

```bash
cp config/config.example.yaml config/config.yaml
```

⚠️ **Important**: `config.yaml` is in `.gitignore` and contains sensitive information (API keys, database passwords). Never commit it to version control!

2. **Edit `config/config.yaml`** with your settings:

```yaml
databases:
  my_database:
    host: localhost
    port: 5432
    database: mydb
    user: postgres
    password_env_var: DB_PASSWORD  # Password from environment
    min_pool_size: 2
    max_pool_size: 10

openai:
  # 方式1: 直接配置 (开发/测试推荐)
  api_key: "sk-your-api-key"
  
  # 方式2: 环境变量 (生产推荐)
  # api_key: null
  # api_key_env_var: "OPENAI_API_KEY"
  
  # 选择 AI 服务:
  
  # OpenAI (默认)
  model: "gpt-4o-mini-2024-07-18"
  base_url: null
  
  # 阿里百炼 (通义千问) - 推荐国内用户
  # model: "qwen-turbo-latest"
  # base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  
  temperature: 0.0
  max_tokens: 2000
  timeout: 30.0
```

3. **Set environment variables** (如果使用方式2):

```bash
export DB_PASSWORD="your_database_password"
export OPENAI_API_KEY="your_openai_api_key"
```

### Running the Server

```bash
# Start the MCP server
python -m postgres_mcp

# Or run directly
python src/postgres_mcp/server.py
```

### Testing with Claude Desktop

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "postgres-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/VibeCoding/Week5",
        "run",
        "python",
        "-m",
        "postgres_mcp"
      ],
      "env": {
        "DB_PASSWORD": "your_password",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

## MCP Tools

### 1. generate_sql

Generate SQL query without executing:

```json
{
  "natural_language": "Show all users created in the last 7 days",
  "database": "my_database"
}
```

**Returns**: Validated SQL + explanation + warnings

### 2. execute_query

Generate and execute SQL query:

```json
{
  "natural_language": "List top 10 products by sales",
  "database": "my_database",
  "limit": 10
}
```

**Returns**: SQL + formatted results (Markdown table) + execution metadata

### 3. list_databases

List all configured databases and their schema information.

### 4. refresh_schema

Manually refresh schema cache for a specific database or all databases.

### 5. query_history ✨ NEW

Retrieve query execution history from logs:

```json
{
  "database": "my_database",
  "status": "success",
  "limit": 50
}
```

**Returns**: Recent query logs with execution details (timestamp, SQL, status, execution time, row count)

## MCP Resources

### schema://{database}

Access complete database schema information.

### schema://{database}/{table}

Access detailed table schema including columns, indexes, and foreign keys.

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -e ".[dev]"

# Or using UV
uv pip install -e ".[dev]"
```

### Running Tests

#### Unit Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=src/postgres_mcp --cov-report=term-missing

# Run integration tests (requires test database)
make up  # Start test databases
pytest tests/integration/ -v
make down  # Stop test databases
```

#### Contract Tests (NL-to-SQL Accuracy) 🎯 **NEW**

契约测试验证自然语言到 SQL 转换的准确性。包含 70 个测试用例，覆盖从基础查询到高级特性。

**快速开始**：

```bash
# 进入契约测试目录
cd tests/contract

# 运行样例测试（3个用例，快速验证，~15秒）
./run_contract_tests.sh sample

# 运行完整测试（70个用例，约4-5分钟）
./run_contract_tests.sh full
```

**测试覆盖**：
- **L1 基础查询**（15个用例）- 目标准确率 ≥95%
- **L2 多表关联**（15个用例）- 目标准确率 ≥90%
- **L3 聚合分析**（12个用例）- 目标准确率 ≥85%
- **L4 复杂逻辑**（10个用例）- 目标准确率 ≥75%
- **L5 高级特性**（8个用例）- 目标准确率 ≥70%
- **S1 安全测试**（10个用例）- 目标准确率 100%

**详细文档**：`tests/contract/README.md`

**注意事项**：
- 测试脚本会自动清除代理设置以避免 API 连接问题
- 完整测试因 API 频率限制需要 4-5 分钟
- 测试结果自动保存到 `/tmp/contract_test_results_*.txt`

### Code Quality

```bash
# Format code
ruff format src/ tests/

# Lint
ruff check src/ tests/ --fix

# Type check
mypy src/
```

### Test Database

Start PostgreSQL test databases with sample data:

```bash
cd fixtures
docker-compose up -d

# Check status
make test-all

# View statistics
make stats

# Stop databases
make down
```

Three test databases are available:
- **ecommerce_small**: E-commerce data (5 tables, ~10K rows)
- **social_medium**: Social network data (8 tables, ~100K rows)  
- **erp_large**: ERP system data (15 tables, ~1M rows)

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      MCP Client                              │
│                 (Claude Desktop, Cursor)                     │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP Protocol (stdio/JSON-RPC)
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   FastMCP Server Layer                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Tools        │  │ Resources    │  │ Prompts      │      │
│  │ (5 tools)    │  │ (2 resources)│  │ (optional)   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Core Business Logic                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  SchemaCache    SQLGenerator    QueryExecutor        │   │
│  │  SQLValidator   PromptBuilder   QueryRunner          │   │
│  │  JSONLWriter (NEW)                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌──────────────────┐  ┌───────────────┐  ┌──────────────┐
│ OpenAI           │  │ Schema        │  │ Asyncpg      │
│ GPT-4o-mini      │  │ Inspector     │  │ Pool         │
└──────────────────┘  └───────┬───────┘  └──────┬───────┘
                              │                  │
                              ▼                  ▼
                      ┌─────────────────────────────┐
                      │   PostgreSQL Database(s)    │
                      └─────────────────────────────┘
```

## Project Structure

```
Week5/
├── src/postgres_mcp/
│   ├── __main__.py              # Entry point
│   ├── server.py                # FastMCP server
│   ├── config.py                # Configuration
│   ├── ai/                      # AI integration
│   │   ├── openai_client.py
│   │   ├── prompt_builder.py
│   │   └── response_parser.py
│   ├── core/                    # Core logic
│   │   ├── sql_generator.py
│   │   ├── sql_validator.py
│   │   ├── schema_cache.py
│   │   └── query_executor.py     # Phase 4
│   ├── db/                      # Database layer
│   │   ├── connection_pool.py
│   │   ├── schema_inspector.py
│   │   └── query_runner.py       # Phase 4
│   ├── mcp/                     # MCP interface
│   │   ├── tools.py              # 5 tools
│   │   └── resources.py          # 2 resources
│   ├── models/                  # Data models
│   │   ├── connection.py
│   │   ├── schema.py
│   │   ├── query.py
│   │   ├── result.py
│   │   └── log_entry.py
│   └── utils/                   # Utilities
│       ├── logging.py
│       ├── validators.py
│       └── jsonl_writer.py       # Phase 4 (NEW)
├── tests/
│   ├── unit/                    # Unit tests (113 passed)
│   │   ├── test_jsonl_writer.py  # Phase 4 (NEW)
│   │   └── ...
│   ├── integration/             # Integration tests
│   ├── contract/                # Contract tests (70 test cases) 🎯 NEW
│   │   ├── test_framework.py    # Test framework classes
│   │   ├── test_l1_basic.py     # L1 基础查询（15个用例）
│   │   ├── test_l2_join.py      # L2 多表关联（15个用例）
│   │   ├── test_l3_aggregate.py # L3 聚合分析（12个用例）
│   │   ├── test_l4_complex.py   # L4 复杂逻辑（10个用例）
│   │   ├── test_l5_advanced.py  # L5 高级特性（8个用例）
│   │   ├── test_s1_security.py  # S1 安全测试（10个用例）
│   │   ├── run_tests.py         # 完整测试执行器
│   │   ├── run_tests_sample.py  # 样例测试执行器
│   │   ├── run_contract_tests.sh # 🚀 测试运行脚本
│   │   └── README.md            # 测试文档
│   └── conftest.py              # Test configuration
├── fixtures/                    # Test databases
│   ├── docker-compose.yml
│   └── init/                    # SQL initialization scripts
├── config/
│   └── config.example.yaml      # Configuration template
├── pyproject.toml               # Project configuration
└── README.md                    # This file
```

## Security

- **Read-Only Operations**: All write operations (INSERT, UPDATE, DELETE, DDL) are blocked using AST-based SQL validation
- **SQL Injection Protection**: Multiple layers of protection including SQLGlot parsing and asyncpg parameterization
- **Timeout Controls**: Query execution timeouts prevent long-running queries
- **Connection Pooling**: Circuit breakers prevent connection exhaustion
- **Dangerous Functions**: Blocks PostgreSQL functions like `pg_read_file`, `pg_ls_dir`, `copy_from`

## Performance

- **SQL Generation**: 95% of requests return in <5 seconds
- **Schema Caching**: 100 tables loaded in <60 seconds
- **Concurrent Queries**: Supports 10+ concurrent requests
- **Memory Efficient**: Schema cache <500MB for 100 tables

## Troubleshooting

### Server won't start

- Check environment variables are set: `DB_PASSWORD`, `OPENAI_API_KEY`
- Verify database connection in `config/config.yaml`
- Check logs for detailed error messages

### SQL generation fails

- Verify OpenAI API key is valid
- Check schema cache is loaded: use `list_databases` tool
- Review natural language query clarity

### Query execution times out

- Default timeout is 30 seconds
- For complex queries, consider optimizing database indexes
- Check database connection pool status

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Run tests before submitting: `pytest tests/`
2. Format code: `ruff format .`
3. Check types: `mypy src/`
4. Follow existing code style and patterns

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- SQL validation powered by [SQLGlot](https://github.com/tobymao/sqlglot)
- Database access via [asyncpg](https://github.com/MagicStack/asyncpg)
- AI powered by [OpenAI](https://openai.com)

## Links

- **Documentation**: [specs/001-postgres-mcp/](../specs/001-postgres-mcp/)
- **Project Status**: [CURRENT_STATUS.md](../specs/001-postgres-mcp/CURRENT_STATUS.md)
- **Quick Start Guide**: [quickstart.md](../specs/001-postgres-mcp/quickstart.md)
- **Test Scripts**: [scripts/README.md](scripts/README.md)
- **Test Reports**: [specs/001-postgres-mcp/testing/](../specs/001-postgres-mcp/testing/)
- **DashScope Guide**: [specs/001-postgres-mcp/testing/README_DASHSCOPE.md](../specs/001-postgres-mcp/testing/README_DASHSCOPE.md)

---

**Status**: Production Ready 🚀  
**Version**: 0.7.0  
**Last Updated**: 2026-01-29  
**Test Status**: 
- ✅ Unit Tests: 113/122 passed (92.6%)
- ✅ Contract Tests: 70 test cases implemented (L1-L5 + S1)
**Coverage**: 90-93% (新代码)
