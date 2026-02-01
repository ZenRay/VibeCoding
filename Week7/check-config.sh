#!/bin/bash

# 配置验证脚本
# 检查所有配置文件是否完整

set -e

echo "🔍 检查 Week7 项目配置..."
echo "================================"
echo ""

cd "$(dirname "$0")"

# 检查后端配置
echo "📋 后端配置检查:"
echo "----------------"

if [ -f "backend/.env" ]; then
    echo "✅ backend/.env 存在"
    
    # 检查必需的配置项
    required_vars=("GEMINI_API_KEY" "AI_MODE" "AI_PROVIDER" "IMAGE_SIZE" "IMAGE_ASPECT_RATIO")
    
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" backend/.env; then
            value=$(grep "^${var}=" backend/.env | cut -d'=' -f2)
            echo "  ✓ ${var}=${value}"
        else
            echo "  ⚠️  ${var} 未设置"
        fi
    done
else
    echo "❌ backend/.env 不存在"
    echo "   请运行: cp backend/.env.example backend/.env"
fi

echo ""

if [ -f "backend/.env.example" ]; then
    echo "✅ backend/.env.example 存在"
else
    echo "❌ backend/.env.example 不存在"
fi

echo ""
echo "📋 前端配置检查:"
echo "----------------"

if [ -f "frontend/vite.config.ts" ]; then
    echo "✅ frontend/vite.config.ts 存在"
else
    echo "❌ frontend/vite.config.ts 不存在"
fi

echo ""
echo "📋 数据文件检查:"
echo "----------------"

if [ -f "outline.yml" ]; then
    echo "✅ outline.yml 存在"
else
    echo "⚠️  outline.yml 不存在 (首次运行时会自动创建)"
fi

echo ""
echo "📋 启动脚本检查:"
echo "----------------"

scripts=("start-backend.sh" "start-dev.sh")
for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
        echo "✅ $script 存在"
    else
        echo "❌ $script 不存在"
    fi
done

echo ""
echo "================================"
echo "✅ 配置检查完成"
echo ""
echo "💡 提示:"
echo "  1. 如需使用真实 AI，请在 backend/.env 中设置:"
echo "     - AI_MODE=real"
echo "     - GEMINI_API_KEY 或 OPENROUTER_API_KEY"
echo "  2. 推荐配置:"
echo "     - IMAGE_SIZE=1K (快速开发)"
echo "     - AI_PROVIDER=openrouter (无区域限制)"
echo "     - OPENROUTER_MODEL=google/gemini-3-pro-image-preview (最佳中文)"
