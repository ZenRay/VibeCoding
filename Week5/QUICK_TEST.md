# MCP 快速测试指南

## 问题修复

### 1. 代理问题 ✅ 已修复
- **原因**: 阿里百炼是国内服务，不需要代理
- **解决**: 移除 HTTP_PROXY/HTTPS_PROXY 环境变量

### 2. Claude CLI 权限问题
- **现象**: Claude 请求读取文件权限
- **解决**: 选择 "Yes, allow reading from 001-postgres-mcp/ during this session"

---

## 快速测试步骤

### 1. 重新启动 MCP 服务器（不使用代理）

```bash
cd /home/ray/Documents/VibeCoding/Week5

# 设置环境（不含代理）
export TEST_DB_PASSWORD="testpass123"
export MCP_CONFIG_PATH="$(pwd)/mcp_config.json"

# 激活虚拟环境
source .venv/bin/activate

# 启动 Claude CLI
claude --mcp-config "$MCP_CONFIG_PATH"
```

---

## 测试用例

### 测试 1: 列出数据库（最简单）

**提示词**:
```
请列出所有可用的数据库
```

**预期**: Claude 会调用 `list_databases` 工具，返回 3 个数据库

---

### 测试 2: 查看数据库 Schema

**提示词**:
```
请显示 ecommerce_small 数据库的表结构
```

**预期**: 显示 5 个表的详细信息

---

### 测试 3: 生成简单 SQL

**提示词**:
```
帮我生成一个 SQL 查询，显示 products 表的所有产品名称和价格
数据库：ecommerce_small
```

**预期**: 生成 `SELECT name, price FROM products;`

---

### 测试 4: 执行查询

**提示词**:
```
执行查询：显示 users 表的前 5 条记录
数据库：ecommerce_small
```

**预期**: 返回格式化的表格数据

---

## 故障排查

### 如果 Claude 无法连接 MCP

1. 检查环境变量:
```bash
echo $MCP_CONFIG_PATH
echo $TEST_DB_PASSWORD
```

2. 手动测试 MCP 服务器:
```bash
cd /home/ray/Documents/VibeCoding/Week5
source .venv/bin/activate
export TEST_DB_PASSWORD="testpass123"
python -m postgres_mcp
```

应该看到：
```
[info] postgres_mcp_server_ready
[info] mcp_server_started_stdio
```

3. 检查数据库:
```bash
cd fixtures
docker compose ps
```

---

## 成功标志

✅ MCP 服务器启动无错误
✅ Claude 能列出 3 个数据库
✅ Claude 能生成 SQL
✅ Claude 能执行查询并返回结果

---

## 测试记录

| 测试项 | 状态 | 备注 |
|--------|------|------|
| MCP 启动 | ⏳ | 待测试（无代理） |
| list_databases | ⏳ | |
| 查看 schema | ⏳ | |
| 生成 SQL | ⏳ | |
| 执行查询 | ⏳ | |

**测试时间**: _____
