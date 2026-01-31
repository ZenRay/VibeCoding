#!/bin/bash

# AI Slide Generator 开发环境启动脚本

echo "🚀 启动 AI Slide Generator 开发环境"
echo ""

# 检查后端虚拟环境
if [ ! -d "backend/.venv" ]; then
    echo "❌ 后端虚拟环境不存在,请先运行:"
    echo "   cd backend && uv venv && source .venv/bin/activate && uv pip install -r requirements.txt"
    exit 1
fi

# 检查前端依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "⚠️  前端依赖未安装,开始安装..."
    cd frontend && npm install && cd ..
fi

# 启动后端 (后台)
echo "📦 启动后端 (http://localhost:8000)..."
cd backend
source .venv/bin/activate
python run.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端
echo "🎨 启动前端 (http://localhost:5173)..."
cd frontend
npm run dev

# 清理: Ctrl+C 时杀死后端进程
trap "kill $BACKEND_PID" EXIT
