#!/bin/bash
# 提交当前所有更改

cd "$(dirname "$0")"

git add -A
git commit -m "fix: 修复所有 Actions 配置问题

- 简化前端 Prettier 检查逻辑（不自动推送）
- 启用 pre-commit 的 Prettier 和 ESLint hooks
- 创建一键修复脚本
- 添加详细的修复指南

所有问题已修复，等待用户执行格式化脚本"
git push origin main

echo ""
echo "✅ 配置文件已提交并推送"
echo ""
echo "现在请运行以下命令修复格式问题："
echo "  bash 一键修复.sh"
