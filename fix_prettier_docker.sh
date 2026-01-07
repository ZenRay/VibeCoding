#!/bin/bash
# 使用 Docker 运行 Prettier 格式化

set -e

cd "$(dirname "$0")"

echo "🐳 使用 Docker 运行 Prettier 格式化..."
echo ""

# 使用 Node 20 镜像运行 Prettier
docker run --rm \
  -v "$(pwd)/frontend:/app" \
  -w /app \
  node:20-alpine \
  sh -c "npm install && npx prettier --write 'src/**/*.{ts,tsx,css}'"

echo ""
echo "✅ 格式化完成！"
echo ""
echo "提交更改："
git add -A
git status --short
echo ""

read -p "确认提交并推送？ (y/n) " -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git commit -m "style: 修复前端 Prettier 格式（使用 Docker）"
    git push origin main
    echo "✅ 完成！"
else
    echo "❌ 取消提交"
fi
