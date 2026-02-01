#!/bin/bash

# AI Slide Generator - Playwright E2E 测试安装脚本

echo "🎯 AI Slide Generator - Playwright E2E 测试"
echo "=========================================="
echo ""

cd "$(dirname "$0")"

echo "📦 1. 安装 Playwright..."
npm install --registry=https://registry.npmmirror.com

if [ $? -ne 0 ]; then
    echo "❌ npm install 失败，尝试使用淘宝镜像..."
    npm install --registry=https://registry.npm.taobao.org
fi

echo ""
echo "🌐 2. 安装 Chromium 浏览器..."
npx playwright install chromium

echo ""
echo "=========================================="
echo "✅ 安装完成！"
echo "=========================================="
echo ""
echo "🚀 运行测试："
echo "  npm test              # 运行所有测试"
echo "  npm run test:ui       # 带 UI 运行（推荐）"
echo "  npm run test:headed   # 显示浏览器"
echo "  npm run test:debug    # 调试模式"
echo ""
echo "📝 注意："
echo "  1. 确保后端服务运行: ../start-backend.sh"
echo "  2. 确保前端服务运行: cd ../frontend && npm run dev"
echo ""
