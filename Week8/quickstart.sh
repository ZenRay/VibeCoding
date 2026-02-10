#!/bin/bash
# Code Agent 快速入门脚本

set -e

echo "🚀 Code Agent 快速入门"
echo "===================="
echo ""

# 检查是否已构建
if [ ! -f "target/release/code-agent" ]; then
    echo "📦 首次运行,正在构建项目..."
    cargo build --release
    echo "✅ 构建完成!"
    echo ""
fi

# 创建别名提示
echo "💡 建议添加别名到你的 shell 配置文件:"
echo "   echo 'alias code-agent=\"$PWD/target/release/code-agent\"' >> ~/.bashrc"
echo "   或"
echo "   echo 'alias code-agent=\"$PWD/target/release/code-agent\"' >> ~/.zshrc"
echo ""

# 显示帮助
echo "📚 可用命令:"
./target/release/code-agent --help
echo ""

# 提示配置
echo "🔧 接下来的步骤:"
echo "   1. 运行: ./target/release/code-agent init --api-key YOUR_API_KEY"
echo "   2. 执行任务: ./target/release/code-agent run \"你的任务描述\""
echo "   3. 启动 TUI: ./target/release/code-agent tui"
echo ""

echo "📖 查看完整文档: README.md"
echo "🚀 快速开始指南: QUICKSTART.md"
