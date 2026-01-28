#!/bin/bash
# MCP 服务器 Claude CLI 测试脚本

set -e

echo "🚀 启动 MCP 集成测试 (Claude CLI)"
echo "=================================="
echo ""

# ⚠️ 重要：清除代理设置（阿里百炼不需要代理）
unset HTTP_PROXY
unset HTTPS_PROXY
unset http_proxy
unset https_proxy
unset ALL_PROXY
unset all_proxy

echo "✅ 已清除代理设置"

# 设置环境变量
export TEST_DB_PASSWORD="testpass123"

echo "✅ 环境变量已设置"

# 检查数据库
echo "📊 检查测试数据库..."
cd /home/ray/Documents/VibeCoding/Week5/fixtures
if ! docker compose ps | grep -q "Up"; then
    echo "❌ 测试数据库未运行，启动中..."
    docker compose up -d
    sleep 5
else
    echo "✅ 测试数据库正在运行"
fi

cd /home/ray/Documents/VibeCoding/Week5

# 激活虚拟环境
echo ""
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 测试 MCP 服务器
echo ""
echo "🧪 测试 MCP 服务器启动..."
timeout 5 python -m postgres_mcp 2>&1 | head -20 &
SERVER_PID=$!
sleep 2

if ps -p $SERVER_PID > /dev/null; then
    echo "✅ MCP 服务器启动成功"
    kill $SERVER_PID 2>/dev/null || true
else
    echo "⚠️  MCP 服务器快速退出（可能正常，因为等待 stdio）"
fi

echo ""
echo "📝 准备 Claude CLI 测试..."
echo ""
echo "MCP 配置文件: $(pwd)/mcp_config.json"
echo ""
echo "=================================="
echo "🎯 启动 Claude CLI 测试"
echo "=================================="
echo ""
echo "测试命令示例："
echo "1. 列出数据库: 使用 list_databases 工具"
echo "2. 获取 schema: 使用 get_schema 工具"
echo "3. 生成 SQL: 显示电商数据库中最近的订单"
echo ""
echo "启动 Claude CLI..."
echo ""

# 使用 MCP 配置启动 Claude
export MCP_CONFIG_PATH="$(pwd)/mcp_config.json"
claude --mcp-config "$MCP_CONFIG_PATH"
