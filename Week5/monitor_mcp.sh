#!/bin/bash
# MCP 实时监控脚本

echo "🔍 MCP 服务器实时监控"
echo "====================="
echo ""

# 查找 MCP 进程
MCP_PID=$(ps aux | grep "[p]ostgres_mcp" | grep python | awk '{print $2}')

if [ -z "$MCP_PID" ]; then
    echo "❌ MCP 服务器未运行"
    exit 1
fi

echo "✅ MCP 服务器运行中 (PID: $MCP_PID)"
echo ""

# 监控网络连接
echo "📊 网络连接:"
netstat -tupn 2>/dev/null | grep $MCP_PID | grep ESTABLISHED || echo "  无网络连接"
echo ""

# CPU 和内存使用
echo "💻 资源使用:"
ps -p $MCP_PID -o %cpu,%mem,vsz,rss,etime,cmd --no-headers
echo ""

# 打开的文件描述符
echo "📁 打开的文件描述符:"
ls -l /proc/$MCP_PID/fd 2>/dev/null | wc -l
echo ""

# 检查是否在等待 I/O
echo "⏳ 进程状态:"
cat /proc/$MCP_PID/status 2>/dev/null | grep "State:"
echo ""

# 实时查看最后的标准输出（如果有日志文件）
if [ -d "/home/ray/Documents/VibeCoding/Week5/logs" ]; then
    echo "📝 最近日志:"
    find /home/ray/Documents/VibeCoding/Week5/logs -type f -mmin -1 -exec tail -5 {} \; 2>/dev/null
fi

echo ""
echo "💡 提示："
echo "  - 如果 State 是 'S (sleeping)' - 正常，等待输入"
echo "  - 如果 CPU % > 50% - 正在处理请求"
echo "  - 如果卡住 - 可能是网络问题或 AI API 超时"
