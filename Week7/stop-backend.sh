#!/bin/bash

# 停止 AI Slide Generator 后端服务

echo "🛑 停止 AI Slide Generator 后端服务..."
echo "======================================"
echo ""

# 查找运行中的 Python 进程
PIDS=$(ps aux | grep "[p]ython.*run.py" | awk '{print $2}')

if [ -z "$PIDS" ]; then
    echo "✅ 没有发现运行中的后端服务"
    exit 0
fi

echo "📍 找到以下进程:"
ps aux | grep "[p]ython.*run.py"
echo ""

# 停止进程
echo "🔪 正在停止进程..."
for PID in $PIDS; do
    echo "  - 停止 PID: $PID"
    kill $PID
    sleep 1
    
    # 如果进程还在运行，强制杀死
    if ps -p $PID > /dev/null 2>&1; then
        echo "  - 强制停止 PID: $PID"
        kill -9 $PID
    fi
done

echo ""
echo "✅ 后端服务已停止"
echo ""

# 验证
if ps aux | grep -q "[p]ython.*run.py"; then
    echo "⚠️ 警告: 仍有进程在运行"
    ps aux | grep "[p]ython.*run.py"
else
    echo "✓ 确认: 所有后端进程已停止"
fi
