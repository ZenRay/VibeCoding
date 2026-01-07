#!/bin/bash
# 检查并提交脚本
# 用法: ./scripts/check-and-commit.sh "commit message"

set -e

COMMIT_MSG="${1:-自动提交}"

echo "🔍 运行本地检查..."
if ./scripts/check-local.sh all; then
    echo "✅ 所有检查通过，准备提交..."
    git add -A
    git commit -m "$COMMIT_MSG"
    echo "✅ 提交完成！运行 'git push' 推送到远程仓库"
else
    echo "❌ 检查失败，请修复问题后重试"
    exit 1
fi
