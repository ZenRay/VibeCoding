# 修复指南

## 快速修复所有问题

在您的终端中运行：

```bash
cd /Users/ZenRay/Documents/AI编程/Projects/Week1
bash 一键修复.sh
```

这个脚本会自动：
1. ✅ 格式化前端代码（Prettier）
2. ✅ 格式化后端代码（Black、isort、Ruff）
3. ✅ 提交所有更改
4. ✅ 推送到 GitHub

## 已修复的 Actions 问题

### 1. 前端 Prettier 检查
- **问题**：Actions 格式化后无法推送（权限问题）
- **修复**：简化检查逻辑，只检查不自动推送
- **解决**：用户在本地格式化后推送

### 2. 后端测试
- **问题**：数据库表不存在（`no such table`）
- **修复**：
  - ✅ 在 `conftest.py` 中导入所有模型
  - ✅ 使用文件数据库替代内存数据库
  - ✅ 添加 autouse fixture 确保表创建

### 3. 标签名称大写
- **问题**：SQLite 没有触发器自动转大写
- **修复**：在 `TagService` 中添加 `_normalize_tag_name()` 方法

### 4. Pre-commit Hooks
- **修复**：启用前端 Prettier 和 ESLint hooks
- **好处**：本地提交时自动格式化和检查

## CI Workflows 配置

### ci.yml（主 CI）
- ✅ Backend Lint & Format Check
- ✅ Backend Tests
- ✅ Frontend Lint & Format Check
- ✅ Frontend Build
- ✅ Docker Build Check
- ✅ Integration Tests

### pre-commit.yml（PR 检查）
- ✅ 运行 pre-commit hooks
- ⚠️  只在 PR 时触发，避免与 ci.yml 重复

### docker-build.yml（Docker 镜像构建）
- ✅ 只在打 tag 时触发（如 v1.0.0）
- ✅ 支持手动触发（workflow_dispatch）

## 下次提交流程

### 方法 1：使用一键修复脚本（推荐）
```bash
bash 一键修复.sh
```

### 方法 2：使用本地检查脚本
```bash
# 先检查
./scripts/check-local.sh all

# 如果失败会自动修复，然后再次检查
./scripts/check-local.sh all

# 检查通过后提交
git add -A
git commit -m "你的提交信息"
git push origin main
```

### 方法 3：手动检查
```bash
# 后端
cd backend
source .venv/bin/activate
black .
isort .
ruff check --fix .
pytest

# 前端
cd ../frontend
npx prettier --write "src/**/*.{ts,tsx,css}"
npm run lint
npm run type-check
npm run build

# 提交
cd ..
git add -A
git commit -m "你的提交信息"
git push origin main
```

## 确认修复成功

运行一键修复脚本后，GitHub Actions 应该：
- ✅ Backend Lint & Format Check - 通过
- ✅ Backend Tests - 通过（35个测试）
- ✅ Frontend Lint & Format Check - 通过
- ✅ Frontend Build - 通过
- ✅ Docker Build Check - 通过

如果仍有问题，查看 Actions 日志并提供错误信息。
