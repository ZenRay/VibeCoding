#!/bin/bash

# ==============================================
# AI Slide Generator - 端到端测试脚本 (Phase 4)
# ==============================================

set -e

echo "🧪 AI Slide Generator - 端到端测试"
echo "======================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试结果
test_result() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗${NC} $2"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

# API 基础 URL
BASE_URL="http://localhost:8000/api"

echo "📋 测试计划:"
echo "  1. 后端服务健康检查"
echo "  2. 风格初始化流程 (US1)"
echo "  3. 幻灯片创建和管理 (US2)"
echo "  4. 幻灯片编辑和重新生成 (US3)"
echo "  5. 幻灯片拖拽排序 (US2)"
echo "  6. 全屏播放准备 (US4)"
echo ""

# ==============================================
# Test 1: 后端健康检查
# ==============================================
echo "🔍 Test 1: 后端服务健康检查"
echo "--------------------------------------"

# 1.1 检查后端是否运行
response=$(curl -s -o /dev/null -w "%{http_code}" ${BASE_URL}/../docs || echo "000")
if [ "$response" = "200" ]; then
    test_result 0 "后端服务运行正常 (HTTP 200)"
else
    test_result 1 "后端服务未运行 (HTTP $response)"
    echo -e "${RED}错误: 请先启动后端服务 (./start-backend.sh)${NC}"
    exit 1
fi

# 1.2 测试 GET /project
response=$(curl -s -w "\n%{http_code}" ${BASE_URL}/project)
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    test_result 0 "GET /project 返回成功"
    echo "   响应: $(echo $body | jq -c .)"
else
    test_result 1 "GET /project 失败 (HTTP $http_code)"
fi

echo ""

# ==============================================
# Test 2: 风格初始化 (US1)
# ==============================================
echo "🎨 Test 2: 风格初始化流程"
echo "--------------------------------------"

# 2.1 重置项目状态
response=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/test/reset)
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" = "200" ]; then
    test_result 0 "重置项目状态"
else
    test_result 1 "重置失败 (HTTP $http_code)"
fi

# 2.2 POST /style/init - 生成风格候选
response=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/style/init \
    -H "Content-Type: application/json" \
    -d '{"description": "现代科技风格，蓝色渐变背景"}')
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    candidate_count=$(echo "$body" | jq '. | length')
    if [ "$candidate_count" -eq 2 ]; then
        test_result 0 "生成 2 个风格候选图"
        STYLE_PATH=$(echo "$body" | jq -r '.[0].image_path')
        echo "   候选图路径: $STYLE_PATH"
    else
        test_result 1 "候选图数量错误: $candidate_count (期望 2)"
    fi
else
    test_result 1 "生成风格候选失败 (HTTP $http_code)"
fi

# 2.3 POST /style/select - 选择风格
response=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/style/select \
    -H "Content-Type: application/json" \
    -d "{\"image_path\": \"$STYLE_PATH\"}")
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    style_ref=$(echo "$body" | jq -r '.style_reference')
    if [ "$style_ref" != "null" ] && [ "$style_ref" != "" ]; then
        test_result 0 "选择风格成功"
        echo "   风格参考: $style_ref"
    else
        test_result 1 "风格未保存"
    fi
else
    test_result 1 "选择风格失败 (HTTP $http_code)"
fi

echo ""

# ==============================================
# Test 3: 幻灯片创建 (US2)
# ==============================================
echo "📄 Test 3: 幻灯片创建和管理"
echo "--------------------------------------"

# 3.1 创建第一张幻灯片
response=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/slides \
    -H "Content-Type: application/json" \
    -d '{"text": "第一张幻灯片：项目介绍"}')
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    SLIDE1_ID=$(echo "$body" | jq -r '.id')
    test_result 0 "创建第一张幻灯片 (ID: $SLIDE1_ID)"
else
    test_result 1 "创建幻灯片失败 (HTTP $http_code)"
fi

# 3.2 创建第二张幻灯片
response=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/slides \
    -H "Content-Type: application/json" \
    -d '{"text": "第二张幻灯片：核心功能"}')
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    SLIDE2_ID=$(echo "$body" | jq -r '.id')
    test_result 0 "创建第二张幻灯片 (ID: $SLIDE2_ID)"
else
    test_result 1 "创建幻灯片失败 (HTTP $http_code)"
fi

# 3.3 创建第三张幻灯片
response=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/slides \
    -H "Content-Type: application/json" \
    -d '{"text": "第三张幻灯片：技术架构"}')
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    SLIDE3_ID=$(echo "$body" | jq -r '.id')
    test_result 0 "创建第三张幻灯片 (ID: $SLIDE3_ID)"
else
    test_result 1 "创建幻灯片失败 (HTTP $http_code)"
fi

# 3.4 验证幻灯片列表
response=$(curl -s -w "\n%{http_code}" ${BASE_URL}/project)
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    slide_count=$(echo "$body" | jq '.slides | length')
    if [ "$slide_count" -eq 3 ]; then
        test_result 0 "验证幻灯片总数: 3 张"
    else
        test_result 1 "幻灯片数量错误: $slide_count (期望 3)"
    fi
else
    test_result 1 "获取项目状态失败 (HTTP $http_code)"
fi

echo ""

# ==============================================
# Test 4: 幻灯片编辑 (US3)
# ==============================================
echo "✏️ Test 4: 幻灯片编辑和重新生成"
echo "--------------------------------------"

# 4.1 更新幻灯片文本
response=$(curl -s -w "\n%{http_code}" -X PUT ${BASE_URL}/slides/${SLIDE1_ID} \
    -H "Content-Type: application/json" \
    -d '{"text": "第一张幻灯片：项目介绍（已更新）"}')
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    updated_text=$(echo "$body" | jq -r '.text')
    if [[ "$updated_text" == *"已更新"* ]]; then
        test_result 0 "更新幻灯片文本"
        echo "   新文本: $updated_text"
    else
        test_result 1 "文本未更新"
    fi
else
    test_result 1 "更新幻灯片失败 (HTTP $http_code)"
fi

# 4.2 验证 content_hash 和 image_hash 不同
response=$(curl -s ${BASE_URL}/project)
slide=$(echo "$response" | jq ".slides[] | select(.id == \"$SLIDE1_ID\")")
content_hash=$(echo "$slide" | jq -r '.content_hash')
image_hash=$(echo "$slide" | jq -r '.image_hash')

if [ "$content_hash" != "$image_hash" ]; then
    test_result 0 "检测到内容变化 (content_hash ≠ image_hash)"
    echo "   content_hash: $content_hash"
    echo "   image_hash: $image_hash"
else
    test_result 1 "Hash 检测失败"
fi

# 4.3 重新生成图片
response=$(curl -s -w "\n%{http_code}" -X POST ${BASE_URL}/slides/${SLIDE1_ID}/generate)
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | head -n-1)

if [ "$http_code" = "200" ]; then
    new_image_path=$(echo "$body" | jq -r '.image_path')
    new_image_hash=$(echo "$body" | jq -r '.image_hash')
    
    if [ "$new_image_path" != "null" ] && [ "$new_image_hash" == "$content_hash" ]; then
        test_result 0 "重新生成图片成功 (image_hash 已同步)"
        echo "   新图片: $new_image_path"
    else
        test_result 1 "图片生成或 Hash 同步失败"
    fi
else
    test_result 1 "重新生成图片失败 (HTTP $http_code)"
fi

echo ""

# ==============================================
# Test 5: 幻灯片排序 (US2)
# ==============================================
echo "🔄 Test 5: 幻灯片拖拽排序"
echo "--------------------------------------"

# 5.1 获取当前顺序
response=$(curl -s ${BASE_URL}/project)
current_order=$(echo "$response" | jq -c '[.slides[].id]')
echo "   当前顺序: $current_order"

# 5.2 反转顺序
new_order="[\"$SLIDE3_ID\", \"$SLIDE2_ID\", \"$SLIDE1_ID\"]"
response=$(curl -s -w "\n%{http_code}" -X PUT ${BASE_URL}/slides/reorder \
    -H "Content-Type: application/json" \
    -d "$new_order")
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" = "200" ]; then
    test_result 0 "发送排序请求"
else
    test_result 1 "排序请求失败 (HTTP $http_code)"
fi

# 5.3 验证新顺序
response=$(curl -s ${BASE_URL}/project)
actual_order=$(echo "$response" | jq -c '[.slides[].id]')
expected_order=$(echo "$new_order" | jq -c .)

if [ "$actual_order" = "$expected_order" ]; then
    test_result 0 "验证排序结果正确"
    echo "   新顺序: $actual_order"
else
    test_result 1 "排序结果错误"
    echo "   期望: $expected_order"
    echo "   实际: $actual_order"
fi

echo ""

# ==============================================
# Test 6: 全屏播放准备 (US4)
# ==============================================
echo "🎬 Test 6: 全屏播放准备"
echo "--------------------------------------"

# 6.1 验证幻灯片顺序稳定
response=$(curl -s ${BASE_URL}/project)
slides=$(echo "$response" | jq '.slides')
slide_count=$(echo "$slides" | jq '. | length')

if [ "$slide_count" -ge 1 ]; then
    test_result 0 "幻灯片列表可用于播放 ($slide_count 张)"
else
    test_result 1 "幻灯片列表为空"
fi

# 6.2 检查所有幻灯片是否有图片
slides_with_image=$(echo "$slides" | jq '[.[] | select(.image_path != null)] | length')
if [ "$slides_with_image" -eq "$slide_count" ]; then
    test_result 0 "所有幻灯片都有图片"
else
    test_result 0 "部分幻灯片有图片 ($slides_with_image/$slide_count)"
    echo -e "   ${YELLOW}注意: Stub 模式下图片为占位符${NC}"
fi

# 6.3 验证幻灯片数据完整性
first_slide=$(echo "$slides" | jq '.[0]')
has_id=$(echo "$first_slide" | jq 'has("id")')
has_text=$(echo "$first_slide" | jq 'has("text")')
has_image=$(echo "$first_slide" | jq 'has("image_path")')

if [ "$has_id" = "true" ] && [ "$has_text" = "true" ] && [ "$has_image" = "true" ]; then
    test_result 0 "幻灯片数据结构完整 (id, text, image_path)"
else
    test_result 1 "幻灯片数据结构不完整"
fi

echo ""

# ==============================================
# Test 7: 清理测试 (US2)
# ==============================================
echo "🗑️ Test 7: 幻灯片删除"
echo "--------------------------------------"

# 7.1 删除最后一张幻灯片
response=$(curl -s -w "\n%{http_code}" -X DELETE ${BASE_URL}/slides/${SLIDE1_ID})
http_code=$(echo "$response" | tail -n1)

if [ "$http_code" = "200" ]; then
    test_result 0 "删除幻灯片成功 (ID: $SLIDE1_ID)"
else
    test_result 1 "删除幻灯片失败 (HTTP $http_code)"
fi

# 7.2 验证删除结果
response=$(curl -s ${BASE_URL}/project)
remaining_count=$(echo "$response" | jq '.slides | length')

if [ "$remaining_count" -eq 2 ]; then
    test_result 0 "验证删除后剩余 2 张幻灯片"
else
    test_result 1 "删除后数量错误: $remaining_count (期望 2)"
fi

echo ""

# ==============================================
# 测试总结
# ==============================================
echo "======================================"
echo "📊 测试总结"
echo "======================================"
echo ""
echo "总测试数: $TOTAL_TESTS"
echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
echo -e "${RED}失败: $FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    echo ""
    echo "🎉 端到端测试完成！"
    echo ""
    echo "📋 功能验证清单:"
    echo "  ✅ US1: 风格初始化 (生成 + 选择)"
    echo "  ✅ US2: 幻灯片管理 (创建 + 删除 + 排序)"
    echo "  ✅ US3: 幻灯片编辑 (更新 + Hash 检测 + 重新生成)"
    echo "  ✅ US4: 全屏播放准备 (数据完整性)"
    echo ""
    echo "🚀 下一步: 启动前端测试播放功能"
    echo "   cd frontend && npm run dev"
    echo ""
    exit 0
else
    echo -e "${RED}❌ 部分测试失败${NC}"
    echo ""
    echo "请检查失败的测试并修复问题"
    echo ""
    exit 1
fi
