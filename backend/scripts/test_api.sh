#!/bin/bash
# API 测试脚本
# 使用 httpie 测试所有 API 端点

BASE_URL="http://localhost:8000/api/v1"
API_URL="http://localhost:8000"

echo "=========================================="
echo "Project Alpha API 测试脚本"
echo "=========================================="
echo ""

# 检查 httpie 是否安装
if ! command -v http &> /dev/null; then
    echo "❌ httpie 未安装"
    echo "安装命令: pip install httpie"
    exit 1
fi

echo "✅ httpie 已安装"
echo ""

# 测试健康检查
echo "1️⃣  测试健康检查..."
http GET $API_URL/health
echo ""

# 创建标签
echo "2️⃣  创建标签..."
TAG1_RESPONSE=$(http POST $BASE_URL/tags name="BACKEND后端" color="#3B82F6")
TAG1_ID=$(echo $TAG1_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo "创建标签 1，ID: $TAG1_ID"
echo ""

TAG2_RESPONSE=$(http POST $BASE_URL/tags name="FRONTEND前端" color="#10B981")
TAG2_ID=$(echo $TAG2_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo "创建标签 2，ID: $TAG2_ID"
echo ""

# 获取标签列表
echo "3️⃣  获取标签列表..."
http GET $BASE_URL/tags
echo ""

# 创建 Ticket
echo "4️⃣  创建 Ticket..."
TICKET_RESPONSE=$(http POST $BASE_URL/tickets \
  title="API 测试 Ticket" \
  description="通过 API 创建的测试 Ticket" \
  tag_ids:="[$TAG1_ID,$TAG2_ID]")
TICKET_ID=$(echo $TICKET_RESPONSE | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')
echo "创建 Ticket，ID: $TICKET_ID"
echo ""

# 获取 Ticket 列表
echo "5️⃣  获取 Ticket 列表..."
http GET $BASE_URL/tickets
echo ""

# 获取单个 Ticket
echo "6️⃣  获取单个 Ticket..."
http GET $BASE_URL/tickets/$TICKET_ID
echo ""

# 更新 Ticket
echo "7️⃣  更新 Ticket..."
http PUT $BASE_URL/tickets/$TICKET_ID \
  title="更新后的标题" \
  description="更新后的描述"
echo ""

# 切换 Ticket 状态
echo "8️⃣  切换 Ticket 状态..."
http PATCH $BASE_URL/tickets/$TICKET_ID/toggle-status
echo ""

# 获取 Ticket（验证状态已切换）
echo "9️⃣  验证状态已切换..."
http GET $BASE_URL/tickets/$TICKET_ID
echo ""

# 搜索 Ticket
echo "🔟 搜索 Ticket..."
http GET $BASE_URL/tickets search=="测试"
echo ""

# 按状态过滤
echo "1️⃣1️⃣  按状态过滤..."
http GET $BASE_URL/tickets status==completed
echo ""

# 软删除 Ticket
echo "1️⃣2️⃣  软删除 Ticket..."
http DELETE $BASE_URL/tickets/$TICKET_ID
echo ""

# 查看回收站
echo "1️⃣3️⃣  查看回收站..."
http GET $BASE_URL/tickets only_deleted==true
echo ""

# 恢复 Ticket
echo "1️⃣4️⃣  恢复 Ticket..."
http POST $BASE_URL/tickets/$TICKET_ID/restore
echo ""

# 删除标签
echo "1️⃣5️⃣  删除标签..."
http DELETE $BASE_URL/tags/$TAG1_ID
echo ""

echo "=========================================="
echo "✅ API 测试完成！"
echo "=========================================="
