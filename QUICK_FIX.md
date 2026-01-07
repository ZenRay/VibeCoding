# 快速修复指南

## 前端 Prettier 格式问题

GitHub Actions 已经格式化了代码，但无法自动推送（权限限制）。

### 方法 1：拉取 Actions 格式化的代码（推荐）

GitHub Actions 创建了提交 `773fb17`，包含格式化后的代码。

**如果在远程仓库看到这个提交**，运行：
```bash
git fetch origin
git pull origin main
```

### 方法 2：本地手动格式化

```bash
cd frontend
npx prettier --write "src/**/*.{ts,tsx,css}"
cd ..
git add -A
git commit -m "style: 修复前端 Prettier 格式"
git push origin main
```

### 方法 3：使用本地检查脚本

```bash
./scripts/check-local.sh frontend
# 如果格式化成功，会自动修复文件
# 然后手动提交
git add -A
git commit -m "style: 修复前端格式"
git push
```

## 后端测试问题

已修复：
- ✅ 数据库表创建问题（改用文件数据库）
- ✅ 标签名称大写转换问题（Service 层处理）

## 下次提交前

```bash
# 运行本地检查
./scripts/check-local.sh all

# 确保通过后再提交
git add -A
git commit -m "你的提交信息"
git push
```
