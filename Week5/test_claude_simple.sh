#!/bin/bash
# 简化的 MCP 测试脚本 - 使用 .claude/config.json

set -e

echo "🚀 启动 MCP 集成测试 (Claude CLI)"
echo "=================================="
echo ""

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

# 显示配置
echo ""
echo "📝 MCP 配置："
cat .claude/config.json | jq '.' 2>/dev/null || cat .claude/config.json

echo ""
echo "=================================="
echo "🎯 启动 Claude CLI"
echo "=================================="
echo ""
echo "配置文件: $(pwd)/.claude/config.json"
echo ""
echo "测试命令示例："
echo "1. 列出数据库: 请列出所有可用的数据库"
echo "2. 查看表: 请显示 ecommerce_small 数据库有哪些表"
echo "3. 生成 SQL: 帮我生成查询所有产品的 SQL"
echo ""
echo "启动 Claude CLI..."
echo ""

# 启动 Claude（会自动读取 .claude/config.json）
cd /home/ray/Documents/VibeCoding/Week5
claude
