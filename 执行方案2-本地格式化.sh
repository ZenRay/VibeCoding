#!/bin/bash
# 方案 2：本地格式化并提交

cd /Users/ZenRay/Documents/AI编程/Projects/Week1

echo "🎨 格式化前端代码..."
cd frontend
npx prettier --write "src/**/*.{ts,tsx,css}"
cd ..

echo ""
echo "📝 提交更改..."
git add -A
git status --short

echo ""
read -p "确认提交？ (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    git commit -m "style: 修复前端 Prettier 格式"
    echo ""
    echo "🚀 推送到远程..."
    git push origin main
    echo ""
    echo "✅ 完成！"
else
    echo "❌ 取消提交"
fi
