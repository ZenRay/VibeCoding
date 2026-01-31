#!/bin/bash

# Phase 2 后端快速启动脚本
# 用于测试 T008 和 T009 的增强端点

set -e

echo "🚀 启动 AI Slide Generator Backend (Phase 2)"
echo "=============================================="
echo ""

# 检查是否在正确的目录
if [ ! -f "backend/app/main.py" ]; then
    echo "❌ 错误: 请在 Week7 目录下运行此脚本"
    exit 1
fi

cd backend

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "⚠️  虚拟环境不存在,正在创建..."
    uv venv
fi

# 激活虚拟环境
echo "📦 激活虚拟环境..."
source .venv/bin/activate

# 检查依赖
echo "🔍 检查依赖..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📥 安装依赖..."
    uv pip install -r requirements.txt
fi

# 检查配置文件
if [ ! -f ".env" ]; then
    echo "⚠️  .env 文件不存在,使用 Stub 模式"
    echo "   (不会调用真实的 Gemini API)"
fi

echo ""
echo "✅ 准备就绪!"
echo ""
echo "📍 启动 FastAPI 服务器..."
echo "   - Host: http://localhost:8000"
echo "   - Docs: http://localhost:8000/docs"
echo "   - Logs: ./api.log"
echo ""
echo "🔧 可测试的端点:"
echo "   - POST /api/style/init (生成风格候选)"
echo "   - POST /api/style/select (选择风格)"
echo ""

# 启动服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
