# 代码质量保证体系

**文档版本**: v1.0  
**创建时间**: 2026-01-08  
**最后更新**: 2026-01-08

## 📋 目录

1. [概述](#概述)
2. [后端代码质量](#后端代码质量)
3. [前端代码质量](#前端代码质量)
4. [Git Hooks](#git-hooks)
5. [CI/CD 检查](#cicd-检查)
6. [最佳实践](#最佳实践)

---

## 概述

Project Alpha 使用多层代码质量保证机制：

```
开发时          提交前          推送后
  ↓              ↓               ↓
编辑器     →  Pre-commit  →  GitHub Actions
(提示)        (检查+修复)      (验证)
```

### 质量标准

- **后端**：Black + isort + Ruff + pytest + mypy
- **前端**：Prettier + ESLint + TypeScript + 构建测试
- **覆盖率**：目标 80%+
- **测试**：单元测试 + 集成测试

---

## 后端代码质量

### Black - 代码格式化

**配置**：`pyproject.toml`

```toml
[tool.black]
line-length = 100
target-version = ['py312']
include = '\.pyi?$'
```

**使用**：
```bash
# 检查
black --check --diff .

# 修复
black .
```

**规则要点**：
- 行长度：100 字符
- 单行类型注解：`str | None`（不拆分）
- 自动添加/删除空行
- 统一引号使用

### isort - 导入排序

**配置**：`pyproject.toml`

```toml
[tool.isort]
profile = "black"
line_length = 100
multi_line_output = 3
include_trailing_comma = true
```

**使用**：
```bash
# 检查
isort --check-only --diff .

# 修复
isort .
```

**排序规则**：
1. 标准库导入
2. 第三方库导入
3. 本地应用导入

### Ruff - 代码检查

**配置**：`pyproject.toml`

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
]
```

**使用**：
```bash
# 检查
ruff check .

# 修复
ruff check --fix .
```

### pytest - 测试

**配置**：`pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "-ra",
]
```

**使用**：
```bash
# 运行所有测试
pytest

# 详细输出
pytest -v

# 覆盖率报告
pytest --cov=app --cov-report=term
pytest --cov=app --cov-report=html

# 运行特定测试
pytest tests/test_api/
pytest tests/test_services/test_tag_service.py::TestTagService::test_create_tag
```

**测试组织**：
```
tests/
├── conftest.py              # 测试配置和 fixtures
├── test_api/                # API 集成测试
│   ├── test_tags.py
│   └── test_tickets.py
└── test_services/           # Service 单元测试
    ├── test_tag_service.py
    └── test_ticket_service.py
```

---

## 前端代码质量

### Prettier - 代码格式化

**配置**：`.prettierrc`

```json
{
  "semi": false,
  "singleQuote": true,
  "tabWidth": 2,
  "trailingComma": "es5",
  "printWidth": 100,
  "arrowParens": "avoid"
}
```

**使用**：
```bash
# 检查
npx prettier --check "src/**/*.{ts,tsx,css}"

# 修复
npx prettier --write "src/**/*.{ts,tsx,css}"
```

**格式要点**：
- 无分号
- 单引号
- 2 空格缩进
- 行长度 100 字符
- 箭头函数避免括号

### ESLint - 代码检查

**配置**：`.eslintrc.cjs`

```javascript
module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  rules: {
    'react-refresh/only-export-components': 'warn',
  },
}
```

**使用**：
```bash
# 检查
npm run lint

# 修复
npm run lint -- --fix
```

### TypeScript - 类型检查

**配置**：`tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "lib": ["ES2020", "DOM"],
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
  }
}
```

**使用**：
```bash
# 类型检查
npm run type-check

# 构建检查
npm run build
```

---

## Git Hooks

### Pre-commit 配置

位置：`.pre-commit-config.yaml`

```yaml
repos:
  # 通用检查
  - repo: https://github.com/pre-commit/pre-commit-hooks
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json

  # 后端检查
  - repo: https://github.com/psf/black
    hooks:
      - id: black
        files: ^backend/
  
  - repo: https://github.com/pycqa/isort
    hooks:
      - id: isort
        files: ^backend/
  
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        files: ^backend/
        args: ['--fix']
```

**注意**：
- 前端 Prettier/ESLint hooks 已禁用（需要 Node 14+）
- 使用 Docker 检查脚本代替

### 安装和使用

```bash
# 安装 pre-commit
pip install pre-commit

# 安装 hooks
pre-commit install

# 手动运行
pre-commit run --all-files
```

---

## CI/CD 检查

### GitHub Actions 工作流

**所有检查都在 Docker 中执行**，确保与本地环境一致。

#### Backend Check (Docker)

```yaml
- name: Run Black format check
  run: |
    docker run --rm \
      -v "${{ github.workspace }}/backend:/app" \
      -w /app \
      python:3.12-slim \
      bash -c "pip install -q black && black --check --diff ."

- name: Run tests
  run: |
    docker run --rm \
      -v "${{ github.workspace }}/backend:/app" \
      -w /app \
      python:3.12-slim \
      bash -c "pip install -q -e '.[dev]' && pytest --cov=app"
```

#### Frontend Check (Docker)

```yaml
- name: Run Prettier check
  run: |
    docker run --rm \
      -v "${{ github.workspace }}/frontend:/app" \
      -w /app \
      node:20-alpine \
      sh -c "npm install && npx prettier --check 'src/**/*.{ts,tsx,css}'"
```

### 本地复现 CI

```bash
# 使用相同的 Docker 命令
docker run --rm \
  -v "$(pwd)/backend:/app" \
  -w /app \
  python:3.12-slim \
  bash -c "pip install -q -e '.[dev]' && black --check . && pytest"
```

---

## 最佳实践

### 1. 提交前检查流程

```bash
# 在 Docker 中检查（推荐）
cd env && ./check-running.sh

# 如果检查失败：
# - 格式问题会自动修复
# - 测试失败需要手动修复代码

# 重新检查确认
./check-running.sh

# 提交
cd .. && git add -A && git commit -m "..." && git push
```

### 2. 代码风格规范

**后端（Python）**：
- 遵循 PEP 8 标准
- 使用 Black 自动格式化
- 类型注解单行：`str | None`
- 导入顺序：stdlib → third-party → local

**前端（TypeScript）**：
- 使用 Prettier 自动格式化
- 单引号、无分号
- 箭头函数简化：`arr.map(x => x * 2)`
- JSX 属性单引号：`className="foo"` → `className='foo'`

### 3. 测试规范

**后端测试**：
- 文件名：`test_*.py`
- 类名：`Test*`
- 函数名：`test_*`
- Fixtures：使用 `conftest.py`
- 覆盖率：目标 80%+

**关键测试配置**：
```python
# tests/conftest.py
from app.models import Tag, Ticket, TicketTag  # 必须导入！

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """确保每个测试前表都存在"""
    Base.metadata.create_all(bind=engine)
    yield
    # 清理数据
```

### 4. 避免常见错误

❌ **不要手动调整格式化输出**
```python
# 错误：手动拆分类型注解
status: str
| None = Query(...)

# 正确：让 Black 自动处理
status: str | None = Query(...)
```

❌ **不要依赖数据库特性**
```python
# 错误：依赖 PostgreSQL 触发器
# 创建标签，期望数据库自动转大写

# 正确：在 Service 层处理
normalized_name = TagService._normalize_tag_name(tag_data.name)
tag = Tag(name=normalized_name, ...)
```

❌ **不要忘记导入模型**
```python
# 错误：只导入 Base
from app.database import Base
Base.metadata.create_all()  # 表不会被创建！

# 正确：导入所有模型
from app.models import Tag, Ticket, TicketTag
Base.metadata.create_all()  # 表会被创建
```

---

## 工具版本

### 后端

| 工具 | 版本 | 用途 |
|------|------|------|
| Python | 3.12 | 运行时 |
| Black | 23.12+ | 格式化 |
| isort | 5.13+ | 导入排序 |
| Ruff | 0.1+ | 代码检查 |
| pytest | 9.0+ | 测试框架 |
| mypy | 1.7+ | 类型检查 |

### 前端

| 工具 | 版本 | 用途 |
|------|------|------|
| Node.js | 20 | 运行时 |
| Prettier | 3.1+ | 格式化 |
| ESLint | 8.56+ | 代码检查 |
| TypeScript | 5.3+ | 类型检查 |

---

## 总结

**代码质量保证的三道防线：**

1. **开发时** - 编辑器 LSP 实时提示
2. **提交前** - Docker 检查脚本自动修复
3. **推送后** - GitHub Actions 验证

**关键：提交前在 Docker 中检查，本地通过 = CI 必通过！** ✅
