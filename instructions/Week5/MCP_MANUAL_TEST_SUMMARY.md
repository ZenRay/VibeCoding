# MCP 人工测试阶段总结

**范围**: Week5 PostgreSQL MCP  
**阶段**: 人工测试（Claude CLI）  
**日期**: 2026-01-29  

---

## 1. 本次人工测试期间的问题汇总

### 1) Claude CLI 读取配置路径不一致
- **现象**: `/mcp` 里只看到 `playwright`，`postgres-mcp` 连接失败。
- **原因**: Claude CLI 实际读取的是用户级配置 `/home/ray/.claude.json`，而不是 `Week5/.claude/config.json`。
- **解决**: 将 `postgres-mcp` 配置写入 `/home/ray/.claude.json` 项目条目。
- **更佳方案**: 明确统一配置入口，文档与脚本统一提示“项目级配置在 `/home/ray/.claude.json`”。

config.json 的详细配置信息
```bash
{
  "mcpServers": {
    "postgres-mcp": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "--directory",
        "～/Documents/VibeCoding/Week5",
        "run",
        "python",
        "-m",
        "postgres_mcp"
      ],
      "env": {
        "TEST_DB_PASSWORD": "testpass123"
      }
    }
  }
}

```
### 2) `mcp_config.json` 过时导致启动失败
- **现象**: 使用 `claude --mcp-config` 时找不到配置或行为异常。
- **原因**: `mcp_config.json` 已废弃，配置改为项目级 `.claude.json`。
- **解决**: 删除 `mcp_config.json`，统一用项目级配置启动 Claude。
- **更佳方案**: 将旧命令从文档中移除，全部改用统一脚本 `debug_agent/start_manual_test.sh`。

### 3) 代理导致 OpenAI/DashScope 连接异常
- **现象**: AI 请求报错、超时、或出现 SOCKS 依赖错误。
- **原因**: 代理环境变量干扰（`HTTP_PROXY/HTTPS_PROXY` 等）。
- **解决**: 测试脚本启动前统一清理代理环境变量。
- **更佳方案**: 在 `.claude.json` 的 MCP env 中明确设置空代理（保持一致）。

### 4) Claude API 侧 404 重试（导致慢）
- **现象**: Claude “thinking” 很久，日志大量 `404 Not Found`。
- **原因**: Claude 自身 API 重试（非 MCP），导致响应慢。
- **解决**: 重启 Claude、确认登录/授权状态；使用 `claude --debug` 观察日志。
- **更佳方案**: 统一测试时先运行 `/mcp`，确认服务联通后再测工具，降低无意义重试。

### 5) `postgres-mcp` YAML 解析错误导致连接失败
- **现象**: `/mcp` 显示 `postgres-mcp · ✘ failed`。
- **原因**: `config.yaml` 缩进错误（`base_url` 多缩进一层）。
- **解决**: 修正 YAML 缩进。
- **更佳方案**: 在 CI 中加入 YAML 校验或最小运行检查。

### 6) 模型权限问题（403 AccessDenied）
- **现象**: `Model access denied`，AI 生成失败。
- **原因**: API Key 没有模型权限（`qwen-turbo-latest` / `qwen-plus-latest`）。
- **解决**: 切换到有权限的模型或更新 key。
- **更佳方案**: 统一建议先用 `qwen-turbo` 验证通路，再切换高阶模型。

### 7) `generate_sql` 返回非 SQL（Struct）被拒绝
- **现象**: `Statement type 'Struct' is not allowed`。
- **原因**: 模型输出 JSON/结构化内容，SQL 解析器判定为 Struct。
- **解决**:
  - 收紧系统提示，强制 JSON 中 `sql` 字段必须是字符串；
  - JSON 解析后如 `sql` 非字符串则直接报错，避免误解析。
- **更佳方案**: 若仍出现，增加模型输出原文采样日志，便于定向优化提示词。

### 8) 读取完整 schema 过慢
- **现象**: “获取完整 schema” 卡住。
- **原因**: 输出量大 + LLM 推理耗时。
- **解决**: 用资源接口 `listMcpResources` / `readMcpResource`，或先用 `list_databases`。
- **更佳方案**: 控制 schema 输出规模，或分页输出。

---

## 1.1 本次测试相关代码改动说明（按文件）

### `src/postgres_mcp/server.py`
- **关联问题**: MCP 在 stdio 模式下被中断/关闭时崩溃；关闭阶段日志写入失败。
- **原因**: stdio 关闭后仍写日志，抛出 `ValueError: I/O operation on closed file`；清理流程中异常未隔离。
- **解决思路**:
  - 在 `server_lifespan` 的 `finally` 中逐项清理资源，失败不影响其余清理；
  - 对关闭阶段日志输出加保护，stdout 关闭时静默退出；
  - `main/run` 捕获异常并避免二次日志导致崩溃。
- **作用**: 提升稳定性，避免“快速退出/关闭时崩溃”。

### `src/postgres_mcp/ai/openai_client.py`
- **关联问题**: `generate_sql` 失败，提示 `Statement type 'Struct' is not allowed`；以及模型返回非 JSON/空 JSON。
- **原因**: 模型输出不是纯 SQL（可能是 JSON/结构体或非 SQL 文本），被 SQL 解析器判定为 Struct。
- **解决思路**:
  - JSON 解析成功但 `sql` 非字符串时直接报错（拒绝结构体）；
  - JSON 解析失败时，尝试从文本中提取 `SELECT/WITH` 语句；
  - 限制从代码块提取时必须包含 `SELECT/WITH`。
- **作用**: 避免把结构化 JSON 当 SQL 解析，提升生成成功率与错误可解释性。

### `src/postgres_mcp/ai/prompt_builder.py`
- **关联问题**: 模型返回 JSON 中 `sql` 不是字符串、或夹带 Markdown。
- **原因**: 系统提示词未强制输出格式，模型输出不稳定。
- **解决思路**:
  - 明确要求输出严格 JSON；
  - `sql` 字段必须是单条 SELECT 字符串；
  - 禁止 Markdown/代码块。
- **作用**: 收敛模型输出格式，降低“Struct”类错误。

### `src/postgres_mcp/core/schema_cache.py`
- **关联问题**: 关闭时后台自动刷新任务打印日志导致崩溃。
- **原因**: stdio 被关闭后继续写日志。
- **解决思路**:
  - 自动刷新协程在 `finally` 中静默退出；
  - 仅在未 shutdown 时记录错误。
- **作用**: 避免关闭阶段异常输出导致进程崩溃。

### `src/postgres_mcp/mcp/tools.py`
- **关联问题**: 工具调用失败后导致服务器退出、或响应不可读。
- **原因**: 缺少顶层错误保护与超时控制。
- **解决思路**:
  - `call_tool` 顶层 try/except；
  - `generate_sql`/`execute_query` 使用 `asyncio.wait_for` 设置超时；
  - 结构化错误消息返回给用户；
  - 记录完整错误类型与堆栈。
- **作用**: 工具出错不致崩溃，且错误可定位。

## 2. 成功测试的推荐启动方式

### ✅ 项目级统一启动脚本（推荐）
```bash
cd VibeCoding/Week5/debug_agent
./start_manual_test.sh
```

### ✅ 启动脚本内容（完整）
```bash
#!/bin/bash
# 项目级 Claude MCP 测试（统一脚本）

set -e

echo "======================================"
echo "PostgreSQL MCP 服务器 - 项目级测试"
echo "======================================"
echo ""

# 1. 清理代理并设置环境变量
echo "🔧 1. 设置环境变量..."
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy ALL_PROXY all_proxy
export TEST_DB_PASSWORD="testpass123"
echo "✅ 已清除代理并设置 TEST_DB_PASSWORD"
echo ""

# 2. 确保测试数据库运行
echo "🔧 2. 检查测试数据库..."
cd VibeCoding/Week5/fixtures
if docker compose ps | grep -q "Up"; then
    echo "✅ 测试数据库运行中"
else
    echo "⚠️  测试数据库未运行，正在启动..."
    docker compose up -d
    sleep 5
fi
echo ""

# 3. 验证项目级 MCP 配置（只读，不修改）
echo "🔧 3. 检查项目 MCP 配置..."
if python3 -c "import json; config=json.load(open('/home/ray/.claude.json')); print('postgres-mcp' in config.get('projects', {}).get('VibeCoding', {}).get('mcpServers', {}))" | grep -q "True"; then
    echo "✅ postgres-mcp 已配置在项目级 .claude.json"
else
    echo "❌ postgres-mcp 未配置（请先在项目级配置中添加）"
    exit 1
fi
echo ""

# 4. 提示测试步骤
echo "======================================"
echo "🎯 Claude 测试步骤"
echo "======================================"
echo ""
echo "【步骤 1】验证 MCP 连接: /mcp"
echo "【步骤 2】基础工具测试: 使用 list_databases 工具"
echo "【步骤 3】AI SQL 生成: 使用 generate_sql 工具"
echo "【步骤 4】查询执行: 使用 execute_query 工具"
echo "【步骤 5】连续稳定性: 重复 list_databases 5 次"
echo ""
echo "⚠️ 如 Claude 已运行，请先 /exit 再重启"
echo ""
echo "⏸️  按 Enter 键启动 Claude CLI..."
read

# 5. 启动 Claude（项目根目录）
cd VibeCoding
claude
```

### ✅ 稳定性预检脚本（可选）
```bash
cd VibeCoding/Week5/debug_agent
./test_stability.sh
```

---

## 2.1 其他测试/监控脚本（意义与用法）

### A) `test_stability.sh`（稳定性预检）
**作用/意义**:
- 在正式 Claude 测试前做一轮预检（数据库、环境变量、代理、MCP 启动、核心单测）
- 发现配置或服务问题时可以提前失败，减少交互测试时间浪费

**使用方法**:
```bash
cd VibeCoding/Week5/debug_agent
./test_stability.sh
```

**脚本内容**（原样）:
```bash
#!/bin/bash
# Week5 MCP 服务器稳定性测试脚本
# 测试修复后的服务器在 Claude CLI 中的表现

set -e

echo "======================================"
echo "MCP 服务器稳定性测试"
echo "======================================"
echo ""

# 1. 检查数据库
echo "📊 1. 检查测试数据库..."
if docker ps --filter "name=mcp-test-db" --format "{{.Names}}" | grep -q "mcp-test-db"; then
    echo "✅ 测试数据库运行中"
else
    echo "❌ 测试数据库未运行"
    echo "启动数据库..."
    cd fixtures && docker compose up -d
    sleep 3
fi
echo ""

# 2. 设置环境变量
echo "🔧 2. 设置环境变量..."
export TEST_DB_PASSWORD="testpass123"
echo "✅ TEST_DB_PASSWORD 已设置"
echo ""

# 3. 清除代理设置（重要！）
echo "🚫 3. 清除代理设置（阿里百炼不需要代理）..."
unset HTTP_PROXY
unset HTTPS_PROXY
unset http_proxy
unset https_proxy
unset ALL_PROXY
unset all_proxy
echo "✅ 代理已清除"
echo ""

# 4. 验证配置
echo "📝 4. 验证 MCP 配置..."
if [ -f "../.claude/config.json" ]; then
    echo "✅ .claude/config.json 存在"
    echo ""
    echo "MCP 服务器配置:"
    cat ../.claude/config.json | jq '.mcpServers."postgres-mcp"'
else
    echo "❌ .claude/config.json 不存在"
    exit 1
fi
echo ""

# 5. 测试 MCP 服务器启动
echo "🚀 5. 测试 MCP 服务器独立启动..."
uv run python -m postgres_mcp > /tmp/mcp_test.log 2>&1 &
MCP_PID=$!
echo "启动 MCP 服务器（PID: $MCP_PID）..."
sleep 2

# 检查日志内容（服务器会快速退出因为等待 stdio，这是正常的）
if grep -q "postgres_mcp_server_ready" /tmp/mcp_test.log; then
    echo "✅ MCP 服务器成功启动并初始化完成"
    
    # 检查是否有错误
    if grep -q "ERROR\|CRITICAL\|Exception" /tmp/mcp_test.log; then
        echo "⚠️ 发现错误日志"
        grep "ERROR\|CRITICAL\|Exception" /tmp/mcp_test.log
    else
        echo "✅ 无错误或异常"
    fi
else
    echo "❌ MCP 服务器启动失败"
    echo ""
    echo "完整日志:"
    cat /tmp/mcp_test.log
    exit 1
fi

# 清理进程（如果还在运行）
if ps -p $MCP_PID > /dev/null 2>&1; then
    kill -TERM $MCP_PID 2>/dev/null || true
    sleep 1
    kill -KILL $MCP_PID 2>/dev/null || true
fi
wait $MCP_PID 2>/dev/null || true

echo ""

# 6. 运行单元测试
echo "🧪 6. 运行核心单元测试..."
source .venv/bin/activate
pytest tests/unit/test_sql_validator.py -v --tb=short -q
echo ""

# 7. 准备 Claude 测试
echo "======================================"
echo "✅ 预检查完成！"
echo "======================================"
echo ""
echo "下一步：在 Claude CLI 中进行实际测试"
echo ""
echo "测试步骤："
echo "1. 启动 Claude:"
echo "   cd VibeCoding"
echo "   claude"
echo ""
echo "2. 测试基础工具（不需要 AI）:"
echo "   使用 list_databases 工具"
echo ""
echo "3. 测试 AI SQL 生成（可能较慢，90秒超时）:"
echo "   使用 generate_sql 工具："
echo "   - natural_language: \"查询所有产品\""
echo "   - database: \"ecommerce_small\""
echo ""
echo "4. 测试查询执行（120秒超时）:"
echo "   使用 execute_query 工具："
echo "   - natural_language: \"显示前5个产品\""
echo "   - database: \"ecommerce_small\""
echo "   - limit: 5"
echo ""
echo "5. 连续测试（验证稳定性）:"
echo "   重复执行 list_databases 5-10 次"
echo ""
echo "预期结果:"
echo "- ✅ 所有查询都返回结果（成功或友好的错误消息）"
echo "- ✅ 服务器不会崩溃或静默退出"
echo "- ✅ 超时的查询会返回清晰的超时消息"
echo "- ✅ 错误的查询会返回详细的错误信息"
echo ""
echo "======================================"
```

### B) `monitor_mcp.sh`（运行期实时监控）
**作用/意义**:
- 快速查看 MCP 进程是否在运行
- 观察 CPU/内存、网络连接、文件描述符、进程状态
- 辅助判断“卡住”是等待 I/O 还是 API 超时

**使用方法**:
```bash
cd VibeCoding/Week5/debug_agent
./monitor_mcp.sh
```

**脚本内容**（原样）:
```bash
#!/bin/bash
# MCP 实时监控脚本

echo "🔍 MCP 服务器实时监控"
echo "====================="
echo ""

# 查找 MCP 进程
MCP_PID=$(ps aux | grep "[p]ostgres_mcp" | grep python | awk '{print $2}')

if [ -z "$MCP_PID" ]; then
    echo "❌ MCP 服务器未运行"
    exit 1
fi

echo "✅ MCP 服务器运行中 (PID: $MCP_PID)"
echo ""

# 监控网络连接
echo "📊 网络连接:"
netstat -tupn 2>/dev/null | grep $MCP_PID | grep ESTABLISHED || echo "  无网络连接"
echo ""

# CPU 和内存使用
echo "💻 资源使用:"
ps -p $MCP_PID -o %cpu,%mem,vsz,rss,etime,cmd --no-headers
echo ""

# 打开的文件描述符
echo "📁 打开的文件描述符:"
ls -l /proc/$MCP_PID/fd 2>/dev/null | wc -l
echo ""

# 检查是否在等待 I/O
echo "⏳ 进程状态:"
cat /proc/$MCP_PID/status 2>/dev/null | grep "State:"
echo ""

# 实时查看最后的标准输出（如果有日志文件）
if [ -d "VibeCoding/Week5/logs" ]; then
    echo "📝 最近日志:"
    find VibeCoding/Week5/logs -type f -mmin -1 -exec tail -5 {} \; 2>/dev/null
fi

echo ""
echo "💡 提示："
echo "  - 如果 State 是 'S (sleeping)' - 正常，等待输入"
echo "  - 如果 CPU % > 50% - 正在处理请求"
echo "  - 如果卡住 - 可能是网络问题或 AI API 超时"
```

---

## 3. 相关配置说明（重要）

### MCP 配置位置
Claude CLI **读取用户级配置**，项目级 MCP 需要写入：
```
 /home/ray/.claude.json
```
（请勿在测试脚本中修改该文件，避免污染用户配置）

### MCP 服务启动命令
在 `.claude.json` 的项目配置中：
```
command: uv
args: ["--directory", "VibeCoding/Week5", "run", "python", "-m", "postgres_mcp"]
```

### AI 模型配置（项目内）
文件：`Week5/config/config.yaml`
```
model: "qwen-plus-latest"
base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
```

---

## 4. 成功测试的核心工具命令

### 1) MCP 连接检查
```
/mcp
```

### 2) list_databases
```
请使用 list_databases 工具列出所有可用的数据库
```

### 3) 读取 schema 资源
```
请列出 MCP 资源（listMcpResources），然后读取资源 schema://ecommerce_small（readMcpResource）
```

### 4) 生成 SQL
```
使用 generate_sql 工具：
- natural_language: "显示所有产品的名称和价格"
- database: "ecommerce_small"
```

### 5) 执行查询
```
使用 execute_query 工具：
- natural_language: "显示前 5 个订单的详细信息"
- database: "ecommerce_small"
- limit: 5
```

---

## 5. 本次测试中出现的问题与处理（简表）

| 问题 | 原因 | 处理方式 | 更佳方案 |
|------|------|----------|----------|
| MCP 不显示 | Claude 读用户级配置 | 写入 `/home/ray/.claude.json` | 统一脚本提醒 |
| `mcp_config.json` 无效 | 已弃用 | 删除并改用项目级配置 | 移除旧命令 |
| 403 AccessDenied | 模型权限不足 | 换模型/更新 key | 先用 `qwen-turbo` |
| Struct 报错 | JSON/非 SQL 输出 | 严格输出 + 解析收紧 | 记录模型原文 |
| 获取 schema 很慢 | 输出量大 | 用资源读取 | 输出分页 |
| Claude 很慢 | Claude API 404 重试 | 重启 Claude/检查登录 | 先 /mcp 再测 |
| YAML 解析失败 | `base_url` 缩进错误 | 修正缩进 | 加入校验 |

---

## 6. 测试过程中的问答汇总

> 以下为测试期间用户提出的问题与结论性回答（已去除重复）：

1. **“单元测试异常”**  
   - 目标测试文件不存在，改为实际的 `tests/unit`/`tests/integration`。

2. **“MCP 服务器快速退出是否正常？”**  
   - stdio 模式下等待输入，快速退出提示可为正常现象，需用 Claude 连接验证。

3. **“Claude tip permissions 怎么处理？”**  
   - 选择允许读项目目录权限即可通过。

4. **“为什么很慢？”**  
   - 主要是 Claude API 404 重试；其次是 schema 大、模型慢。

5. **“Model access denied / 403”**  
   - API Key 无该模型权限，需换模型或更新 key。

6. **“mcp_config.json 还能用吗？”**  
   - 不能，已弃用，改用 `/home/ray/.claude.json`。

7. **“如何看 Claude 日志？”**  
   - `tail -n 200 /home/ray/.claude/debug/latest` 或 `claude --debug`。

8. **“提示词是否可用？”**  
   - 需要改为明确工具调用格式（已修订）。

9. **“Struct 报错正常吗？”**  
   - 不正常，属于模型输出非 SQL；已收紧输出格式并修复解析。

10. **“需要重启服务吗？”**  
   - 需要，修改配置与服务逻辑后必须重启 Claude/MCP。

---

## 7. 清理与后续建议

- **文档与脚本已统一放入**: `Week5/debug_agent/`
- **后续测试统一入口**: `./debug_agent/start_manual_test.sh`
- **Claude 调试**: `claude --debug`
- **监控脚本**: `./debug_agent/monitor_mcp.sh`

---

## 8. 结论

本次人工测试已完成初步验证，MCP 基础连接与工具调用成功；  
已定位并解决多个阻断问题（配置路径、代理、YAML、模型权限、Struct 报错）。  
剩余工作主要集中在 **模型输出稳定性与 Claude API 侧 404 重试** 的治理。

