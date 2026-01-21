#!/bin/bash
# Git 提交脚本 - 自动处理所有更改

set -e

echo "=========================================="
echo "  Git 提交流程"
echo "=========================================="
echo ""

cd /Users/ZenRay/Documents/AICodingGeekTime/Projects

# 步骤 1: 显示当前状态
echo "【1/4】当前分支和状态..."
git branch --show-current
echo ""
git status --short
echo ""

# 步骤 2: 暂存所有更改
echo "【2/4】暂存所有更改..."
git add -A
echo "✅ 已暂存所有文件"
echo ""

# 步骤 3: 显示将要提交的内容
echo "【3/4】将要提交的更改:"
git diff --cached --stat
echo ""

# 步骤 4: 执行提交
echo "【4/4】执行提交..."

git commit -m "feat: 优化 UI 布局 - SQL 编辑器和 AI 功能改为 Tab 切换

主要改进:
- 将 SQL 编辑器和 AI 生成 SQL 合并为一个卡片，使用 Tab 切换
- 执行和清除按钮移至编辑器下方，与编辑器同行显示
- AI 生成 SQL 成功后自动切换到编辑器 Tab
- 改进前端错误处理，正确解析后端错误信息
- 修复 api.ts 中 Error 对象传入 object 的问题

技术细节:
- 新增 activeEditorTab 状态管理 Tab 切换
- 使用 Ant Design Card 组件的 tabList 属性
- 优化错误拦截器，处理 FastAPI 结构化错误响应
- 添加 OpenAI 配置检查和诊断脚本

文件修改:
- Week2/frontend/src/pages/DatabasePage.tsx: Tab 布局和状态管理
- Week2/frontend/src/services/api.ts: 错误处理优化
- Week2/check_openai.sh: OpenAI 配置检查脚本
- Week2/configure_openai.sh: OpenAI 配置向导
- Week2/check_model.py: 模型配置检查
- Week2/UI_UPDATE_TABS.md: 界面优化说明文档"

echo ""
echo "=========================================="
echo "✅ 提交完成！"
echo "=========================================="
echo ""

# 显示最新的提交
echo "最新提交:"
git log -1 --oneline
echo ""

echo "下一步（可选）："
echo "  1. 推送到远程: git push"
echo "  2. 查看提交历史: git log --oneline -5"
echo "  3. 查看提交详情: git show"
