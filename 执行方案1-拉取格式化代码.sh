#!/bin/bash
# 方案 1：从 GitHub 拉取格式化后的代码

cd /Users/ZenRay/Documents/AI编程/Projects/Week1

echo "📥 拉取远程更新..."
git fetch origin

echo ""
echo "📋 查看远程提交历史..."
git log origin/main --oneline -5

echo ""
echo "📋 查看本地提交历史..."
git log --oneline -5

echo ""
echo "🔄 拉取并合并远程代码..."
git pull origin main --no-rebase

echo ""
echo "✅ 完成！请检查是否成功合并。"
echo ""
echo "如果成功，运行以下命令推送："
echo "  git push origin main"
