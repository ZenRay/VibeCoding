#!/bin/bash
# 验证前后端交互脚本

echo "=========================================="
echo "前后端交互验证"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8000/api/v1"
FRONTEND_URL="http://localhost:5173"

echo "1️⃣  检查服务状态..."
cd "$(dirname "$0")/env"
docker compose ps
echo ""

echo "2️⃣  测试后端 API（直接访问）..."
echo "  获取标签列表："
curl -s $BASE_URL/tags | python3 -m json.tool | head -15
echo ""

echo "  获取 Ticket 列表："
curl -s $BASE_URL/tickets | python3 -m json.tool | head -20
echo ""

echo "3️⃣  测试前端页面..."
echo "  前端页面可访问："
curl -s $FRONTEND_URL | head -5
echo ""

echo "4️⃣  检查后端日志（最近的 API 请求）..."
docker compose logs backend --tail 10 | grep -E "GET|POST" | tail -5
echo ""

echo "5️⃣  检查前端日志（错误信息）..."
docker compose logs frontend --tail 20 | grep -E "error|Error|failed|Failed" | tail -5
echo ""

echo "=========================================="
echo "✅ 验证完成！"
echo ""
echo "访问前端页面查看数据："
echo "  http://localhost:5173"
echo ""
echo "如果数据没有显示，请："
echo "  1. 打开浏览器开发者工具（F12）"
echo "  2. 查看 Console 标签页是否有错误"
echo "  3. 查看 Network 标签页检查 API 请求"
echo "=========================================="
