# Git 工作流和代码质量保证

**文档版本**: v1.0  
**创建时间**: 2026-01-08  
**最后更新**: 2026-01-08

## 📋 目录

1. [Pre-commit Hooks](#pre-commit-hooks)
2. [GitHub Actions CI/CD](#github-actions-cicd)
3. [使用指南](#使用指南)

---

## Pre-commit Hooks

### 功能说明

Pre-commit hooks 在每次 Git 提交前自动运行代码检查，确保代码质量。

### 已配置的检查项

#### 通用检查
- ✅ **trailing-whitespace** - 删除行尾空白
- ✅ **end-of-file-fixer** - 确保文件末尾有换行符
- ✅ **check-yaml** - YAML 文件语法检查
- ✅ **check-json** - JSON 文件语法检查
- ✅ **check-toml** - TOML 文件语法检查
- ✅ **check-added-large-files** - 检查大文件（>1MB）
- ✅ **check-merge-conflict** - 检查合并冲突标记
- ✅ **check-case-conflict** - 检查文件名大小写冲突
- ✅ **detect-private-key** - 检测私钥泄露
- ✅ **mixed-line-ending** - 统一换行符（LF）

#### 后端 Python 检查
- ✅ **Black** - 代码格式化（行长度 100）
- ✅ **isort** - 导入排序（Black 兼容模式）
- ✅ **Ruff** - 快速代码检查（自动修复）
- ✅ **mypy** - 类型检查（宽松模式）

#### 前端 TypeScript/React 检查
- ✅ **Prettier** - 代码格式化（JS/TS/JSON/CSS/MD）
- ✅ **ESLint** - 代码质量检查（自动修复）

#### 文档和配置检查
- ✅ **markdownlint** - Markdown 文件检查
- ✅ **hadolint** - Dockerfile 检查
- ✅ **yamllint** - YAML 文件检查（docker-compose.yml）

### 安装和配置

#### 1. 安装 pre-commit

```bash
# 使用 pip 安装
pip install pre-commit

# 或使用 UV（推荐）
uv pip install pre-commit
```

#### 2. 安装 Git hooks

```bash
# 在项目根目录执行
pre-commit install

# 安装到 .git/hooks/pre-commit
```

#### 3. 手动运行所有检查

```bash
# 检查所有文件
pre-commit run --all-files

# 检查特定文件
pre-commit run --files backend/app/main.py frontend/src/App.tsx
```

#### 4. 更新 hooks

```bash
# 更新到最新版本
pre-commit autoupdate
```

### 跳过 hooks（不推荐）

```bash
# 跳过 pre-commit hooks（紧急情况）
git commit --no-verify -m "紧急修复"
```

---

## GitHub Actions CI/CD

### 工作流说明

#### 1. CI 工作流 (`ci.yml`)

在每次 push 和 pull request 时运行：

**后端检查**:
- ✅ **backend-lint** - Black、isort、Ruff、mypy 检查
- ✅ **backend-test** - 运行单元测试和集成测试
- ✅ **coverage** - 代码覆盖率报告（上传到 Codecov）

**前端检查**:
- ✅ **frontend-lint** - ESLint、Prettier、TypeScript 类型检查
- ✅ **frontend-build** - 构建检查（确保可以成功构建）

**Docker 检查**:
- ✅ **docker-build** - 验证 Dockerfile 可以成功构建

**集成测试**:
- ✅ **integration-test** - 在真实数据库环境中运行集成测试（仅 main 分支）

#### 2. Pre-commit 工作流 (`pre-commit.yml`)

在 pull request 和 push 时运行 pre-commit 检查，确保代码符合规范。

#### 3. Docker 构建和推送 (`docker-build.yml`)

在以下情况触发：
- ✅ 推送到 `main` 分支
- ✅ 创建版本标签（`v*.*.*`）
- ✅ 手动触发（workflow_dispatch）

自动构建并推送 Docker 镜像到 GitHub Container Registry。

### 工作流状态徽章

在 README.md 中添加：

```markdown
![CI](https://github.com/your-username/project-alpha/workflows/CI/badge.svg)
![Pre-commit](https://github.com/your-username/project-alpha/workflows/Pre-commit/badge.svg)
```

---

## 使用指南

### 开发工作流

#### 1. 克隆项目

```bash
git clone https://github.com/your-username/project-alpha.git
cd project-alpha
```

#### 2. 安装 pre-commit hooks

```bash
# 安装 pre-commit
pip install pre-commit
# 或
uv pip install pre-commit

# 安装 hooks
pre-commit install
```

#### 3. 开发代码

```bash
# 创建功能分支
git checkout -b feature/your-feature

# 编写代码...

# 提交前会自动运行 pre-commit hooks
git add .
git commit -m "feat: 添加新功能"
# Pre-commit hooks 会自动运行并修复问题
```

#### 4. 推送代码

```bash
# 推送到远程仓库
git push origin feature/your-feature

# GitHub Actions 会自动运行 CI 检查
```

#### 5. 创建 Pull Request

- 创建 PR 后，GitHub Actions 会自动运行所有检查
- 确保所有检查通过后再合并

### 提交信息规范

推荐使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type)**:
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```bash
git commit -m "feat(tickets): 添加搜索功能"
git commit -m "fix(api): 修复标签过滤问题"
git commit -m "docs: 更新 README"
```

### 常见问题

#### 问题 1: Pre-commit hooks 运行失败

**错误**: `black....................................................................Failed`

**解决方案**:
```bash
# 手动运行 Black 格式化
cd backend
black .

# 然后重新提交
git add .
git commit -m "style: 格式化代码"
```

#### 问题 2: 某些检查需要跳过

**解决方案**: 在 `.pre-commit-config.yaml` 中注释掉不需要的检查，或使用 `SKIP` 环境变量：

```bash
SKIP=mypy git commit -m "feat: 新功能"
```

#### 问题 3: GitHub Actions 失败

**检查步骤**:
1. 查看 Actions 标签页的详细日志
2. 本地运行相同的命令：
   ```bash
   # 后端检查
   cd backend
   black --check .
   ruff check .
   
   # 前端检查
   cd frontend
   npm run lint
   npm run type-check
   ```

#### 问题 4: Docker 构建失败

**检查步骤**:
```bash
# 本地测试 Docker 构建
cd env
docker compose build backend
docker compose build frontend
```

### 最佳实践

1. **提交前运行检查**:
   ```bash
   pre-commit run --all-files
   ```

2. **保持 hooks 更新**:
   ```bash
   pre-commit autoupdate
   ```

3. **查看覆盖率**:
   ```bash
   cd backend
   pytest --cov=app --cov-report=html
   open htmlcov/index.html
   ```

4. **本地测试 CI**:
   ```bash
   # 使用 act（GitHub Actions 本地运行器）
   act -j backend-lint
   ```

---

## 配置说明

### Pre-commit 配置位置

- `.pre-commit-config.yaml` - 项目根目录

### GitHub Actions 配置位置

- `.github/workflows/ci.yml` - CI 工作流
- `.github/workflows/pre-commit.yml` - Pre-commit 检查
- `.github/workflows/docker-build.yml` - Docker 构建和推送

### 相关配置文件

**后端**:
- `backend/pyproject.toml` - Black、isort、Ruff、mypy 配置

**前端**:
- `frontend/.eslintrc.cjs` - ESLint 配置
- `frontend/.prettierrc` - Prettier 配置
- `frontend/tsconfig.json` - TypeScript 配置

---

**状态**: ✅ Git 工作流和 CI/CD 已配置完成
