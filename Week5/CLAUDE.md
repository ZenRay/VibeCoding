# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作提供指导。

**项目根目录**: `~/Documents/VibeCoding/Week5`
**包管理器**: UV (Python)
**最后更新**: 2026-01-28

---

## 项目概述

Week5 是一个使用 UV 管理的 Python 项目，强调高代码质量、测试质量和性能，遵循 Python 最佳实践和 SOLID/DRY 原则。

本目录使用 **speckit** 框架进行规格驱动开发，集成了规格说明、计划和实现工作流程的工具。

### 当前活跃项目

**001-postgres-mcp** - PostgreSQL 自然语言查询 MCP 服务器
- **状态**: 规格阶段（已完成）
- **分支**: `001-postgres-mcp`
- **文档**: `~/Documents/VibeCoding/specs/001-postgres-mcp/`
- **描述**: 基于 Python 的 MCP 服务器，允许用户使用自然语言查询 PostgreSQL 数据库，利用 OpenAI GPT-4o-mini 模型生成 SQL，支持 schema 缓存、安全验证和查询执行

---

## 开发环境设置

### 前置要求

- Python 3.11+（推荐 3.12）
- [UV 包管理器](https://github.com/astral-sh/uv)
- Git

### 虚拟环境

**环境路径**: `~/Documents/VibeCoding/Week5/.venv`

项目使用 UV 管理的本地虚拟环境。所有 Python 依赖项都安装在这个隔离的环境中。

### 初始化设置

```bash
# 进入项目根目录
cd ~/Documents/VibeCoding/Week5

# 安装 UV（如果尚未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate  # Linux/Mac 系统
# 或者: .venv\Scripts\activate  # Windows 系统

# 安装依赖（pyproject.toml 存在后）
uv pip install -e ".[dev,test]"
```

---

## 常用命令

### 开发

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行测试
pytest

# 运行测试并生成覆盖率报告
pytest --cov=. --cov-report=html --cov-report=term

# 运行特定测试文件
pytest tests/test_module.py

# 运行特定测试
pytest tests/test_module.py::test_function_name

# 运行代码检查
ruff check .

# 运行格式检查
ruff format --check .

# 自动修复代码检查问题
ruff check --fix .

# 自动格式化代码
ruff format .

# 类型检查
mypy .

# 运行所有质量检查
ruff check . && ruff format --check . && mypy . && pytest
```

### Speckit 工作流

```bash
# 1. 创建功能规格说明
# (使用斜杠命令: /speckit.specify <功能描述>)

# 2. 创建实现计划
# (使用斜杠命令: /speckit.plan)

# 3. 生成任务分解
# (使用斜杠命令: /speckit.tasks)

# 4. 执行实现
# (使用斜杠命令: /speckit.implement)

# 5. 将任务转换为 GitHub issues（可选）
# (使用斜杠命令: /speckit.taskstoissues)
```

---

## 项目治理原则

本项目遵循项目宪章（完整版本见 `.cursor/constitution.md`）。以下是核心强制原则：

### 代码质量门禁（非妥协）

**强制要求**：
- **类型覆盖率**: 必须达到 **99%+** 的静态类型检查覆盖率（mypy strict 模式）
- **代码格式化**: 必须严格执行 **ruff** 格式化标准
- **Docstring**: 所有公共函数、类和模块必须包含标准格式的英文 Docstring
  - 必须包含 `Args`、`Returns`、`Raises` 部分
  - 使用 `----------` 分隔线
  - 建议包含 `Example` 部分

**Docstring 示例**：
```python
def calculate_discount(price: float, coupon: Coupon) -> float:
    """
    Calculate discounted price after applying coupon.

    Args:
    ----------
        price: Original price before discount
        coupon: Coupon object with discount information

    Returns:
    ----------
        Final price after applying discount

    Raises:
    ----------
        ValueError: If price is negative or coupon is invalid

    Example:
    ----------
        >>> coupon = Coupon(code="SAVE20", discount_percent=20)
        >>> calculate_discount(100.0, coupon)
        80.0
    """
    pass
```

### 测试先行（TDD，非妥协）

**强制要求**：
- 必须先编写**失败的单元测试**，再进行功能实现
- 严格遵循 **红-绿-重构** 循环
- 所有 PR 必须包含对应的测试代码
- 测试覆盖率目标：关键业务逻辑 ≥ 90%

### 架构完整性（非妥协）

**强制要求**：
- 坚持 **领域驱动的模块化设计**（DDD）
- 每个功能域必须具备清晰的边界和独立的职责
- 跨域交互必须通过明确定义的接口或事件进行
- 严禁循环依赖

### 文件操作闭环（非妥协）

**强制要求**：
- 所有文件创建、修改、检查操作必须形成**闭环**
- 严禁过度创建新文档，必须在原有文档上迭代改进
- 文档更新必须使用**原地修改**（in-place update）
- ✅ 正确：创建 `spec.md` → 检查 → 更新 `spec.md`
- ❌ 错误：创建 `spec.md` → 检查 → 创建 `spec_v2.md`

### 文档语言规范

**代码层面（必须英文）**：
- 变量/函数/类命名、代码注释、Docstring、日志消息
- API 端点路径、参数名

**文档层面（使用中文）**：
- 需求文档、设计文档、README、CHANGELOG
- 代码审查评论、Issue/PR 描述
- 项目计划、技术方案、架构设计文档

---

## 代码规范与标准

### Python 最佳实践

**遵循 PEP 8 和 Python 惯用法**：
- 函数和变量使用 `snake_case`
- 类使用 `PascalCase`
- 常量使用 `UPPER_CASE`
- 最大行长度：100 字符（代码），ruff format 默认 88
- 所有函数签名使用类型提示
- 优先使用 pathlib 而不是 os.path
- 使用上下文管理器（`with` 语句）进行资源管理
- 在清晰可读时使用列表/字典/集合推导式

**SOLID 原则**：
- **单一职责**: 每个类/函数有一个明确的目的
- **开闭原则**: 使用协议/ABC 进行扩展而不修改
- **里氏替换**: 子类型必须可替换基类型
- **接口隔离**: 保持接口最小化和专注
- **依赖倒置**: 依赖抽象而非具体实现

**DRY（不要重复自己）**：
- 将重复的逻辑提取到函数/类中
- 使用装饰器处理横切关注点
- 适当利用继承和组合

### 代码组织

```
Week5/
├── src/                    # 源代码
│   └── {project_name}/     # 主包
│       ├── __init__.py
│       ├── core/           # 核心业务逻辑
│       ├── models/         # 数据模型
│       ├── services/       # 服务层
│       ├── utils/          # 工具函数
│       └── cli/            # CLI 接口（如适用）
├── tests/                  # 测试套件
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── conftest.py        # Pytest 固件
├── docs/                   # 文档
├── pyproject.toml          # 项目配置
├── uv.lock                # 依赖锁定文件
├── README.md
└── CLAUDE.md              # 本文件
```

### 错误处理

- 使用具体的异常类型，避免裸 `except:`
- 为领域特定错误创建自定义异常
- 使用 `raise ... from e` 保留异常链
- 用适当的上下文记录错误
- 在系统边界验证输入

### 性能

- 对大数据集使用生成器
- 对昂贵的纯函数使用 `functools.lru_cache`
- 优化前先进行性能分析（`cProfile`、`line_profiler`）
- 对 I/O 密集型操作考虑使用 `asyncio`
- 使用 `dataclasses` 或 `pydantic` 进行数据验证

---

## 测试标准

### 测试质量要求

- 最低 90% 代码覆盖率
- 所有公共 API 必须有测试
- 遵循 AAA 模式：Arrange（准备）、Act（执行）、Assert（断言）
- 使用描述性测试名称：`test_<function>_<scenario>_<expected>`
- 参数化测试以减少重复（`pytest.mark.parametrize`）
- 使用固件进行通用设置（`conftest.py`）
- 正确模拟外部依赖
- 测试边界情况和错误条件

### 测试组织

```python
# 良好的测试结构
def test_calculate_discount_with_valid_coupon_returns_discounted_price():
    """测试应用有效优惠券能正确减少价格。"""
    # Arrange（准备）
    original_price = 100.0
    coupon = Coupon(code="SAVE20", discount_percent=20)

    # Act（执行）
    discounted_price = calculate_discount(original_price, coupon)

    # Assert（断言）
    assert discounted_price == 80.0
```

### 测试类型

- **单元测试**: 隔离测试单个函数/类
- **集成测试**: 测试组件交互
- **契约测试**: 验证 API 契约（如适用）
- **性能测试**: 验证性能要求

---

## 依赖管理

### 使用 UV

```bash
# 添加依赖
uv pip install package-name

# 添加开发依赖（用于 pyproject.toml）
# 手动编辑 pyproject.toml，添加到 [project.optional-dependencies.dev]

# 更新依赖
uv pip install --upgrade package-name

# 同步环境与锁定文件
uv pip sync

# 生成锁定文件
uv lock
```

### 依赖指南

- 固定确切版本以保证可重现性
- 分离生产和开发依赖
- 最小化依赖数量
- 尽可能优先使用标准库
- 记录每个依赖的必要性

---

## Git 工作流（非妥协原则）

### 分支命名

功能分支遵循模式：`<编号>-<简短名称>`

示例：`001-user-authentication`、`002-data-export`

### 标准提交流程

**完整工作流（强制执行）**：

```bash
# 1. 代码格式化（git add 前）
ruff format .

# 2. 暂存更改
git add src/ tests/ docs/

# 3. 代码质量检查（git commit 前）
ruff check src/ tests/ --fix
mypy src/
pytest tests/ --cov=src

# 4. 提交代码（Conventional Commits）
git commit -m "feat(module): 描述变更内容"

# 5. 推送代码（必须明确指定远程和分支）
git push origin feature/branch-name
```

### 提交消息规范（Conventional Commits）

**格式**: `<类型>(<范围>): <描述>`

**类型**（必选）：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式化（不影响功能）
- `refactor`: 重构（不修复 bug，不添加功能）
- `test`: 测试相关
- `chore`: 构建/工具相关
- `perf`: 性能优化

**范围**（可选但推荐）：
- 模块名称: `token`, `storage`, `config`, `cli`, `core`, `utils` 等

**描述**（必选）：
- 清晰简洁（≤ 50 字符为佳）
- 使用祈使句（"添加"而非"添加了"）
- 中文或英文保持一致
- 首字母小写

**示例**：
```
feat(token): 实现 Token 自动刷新机制

- 添加刷新阈值配置（默认 80%）
- 实现双重检查锁防止重复刷新
- 添加刷新失败重试机制（最多 3 次）

Closes #42
```

```
fix(storage): 修复 PostgreSQL 连接池泄漏

连接未正确释放导致池耗尽，现已修复:
- 使用 context manager 确保连接释放
- 添加连接超时检测

Fixes #127
```

### Push 规范（强制要求）

**必须明确指定**：
```bash
✅ git push origin feature/token-refresh  # 正确
✅ git push origin main --tags            # 正确
❌ git push                               # 错误：缺少远程和分支
❌ git push origin                        # 错误：缺少分支
```

**特殊情况**：
- 首次推送：`git push -u origin feature/xxx`
- 强制推送：使用 `--force-with-lease` 而非 `--force`

**禁止行为**：
- Agent/脚本禁止自动 push，必须由用户明确授权

---

## Speckit 框架

本项目使用 speckit 进行规格驱动开发。关键概念：

### 工作流阶段

1. **规格说明** (`/speckit.specify`)：定义"做什么"和"为什么"（无实现细节）
2. **计划** (`/speckit.plan`)：定义"如何做"（技术栈、架构、文件）
3. **任务** (`/speckit.tasks`)：分解为可执行任务
4. **实现** (`/speckit.implement`)：遵循 TDD 执行任务

### 关键文件

- `.specify/memory/constitution.md`: 项目治理原则
- `.specify/templates/`: 规格、计划、任务、检查清单的模板
- `.specify/scripts/`: 工作流自动化脚本
- `specs/<feature-id>-<name>/`: 功能文档
  - `spec.md`: 功能规格说明（业务需求）
  - `plan.md`: 技术实现计划
  - `tasks.md`: 任务分解
  - `data-model.md`: 实体和关系定义
  - `contracts/`: API 契约和测试规范

### 可用的斜杠命令

- `/speckit.specify <描述>`: 创建功能规格说明
- `/speckit.plan`: 生成技术实现计划
- `/speckit.tasks`: 创建任务分解
- `/speckit.implement`: 执行实现
- `/speckit.clarify`: 为规格提出澄清问题
- `/speckit.analyze`: 跨工件一致性检查
- `/speckit.checklist`: 生成自定义检查清单
- `/speckit.taskstoissues`: 将任务转换为 GitHub issues
- `/speckit.constitution`: 更新项目宪章

---

## Project Configuration

### pyproject.toml Structure

```toml
[project]
name = "project-name"
version = "0.1.0"
description = "Project description"
requires-python = ">=3.11"
dependencies = [
    # Production dependencies
]

[project.optional-dependencies]
dev = [
    "ruff>=0.1.0",
    "mypy>=1.7",
    "pytest>=7.4",
    "pytest-cov>=4.1",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP", "YTT", "S", "B", "A", "C4", "T20"]
ignore = []

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --strict-markers --cov=src --cov-report=term-missing"

[tool.coverage.run]
source = ["src"]
omit = ["*/tests/*", "*/__pycache__/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

---

## 强制检查清单

每个功能开发必须通过以下检查：

### 设计阶段
- [ ] 技术栈符合 Python 3.X 要求
- [ ] 模块依赖关系无循环（DDD 设计）
- [ ] 响应结构设计包含业务状态码、请求 ID、错误上下文
- [ ] 设计文档遵循闭环操作（原地更新）

### 开发阶段
- [ ] 测试先行完成（TDD 红-绿-重构）
- [ ] 代码质量门禁通过（99%+ 类型覆盖率，ruff 格式化）
- [ ] 所有公共 API 包含标准 Docstring
- [ ] 代码文件在原地迭代更新
- [ ] Git 提交前完成三项检查（ruff/mypy/pytest）

### 代码审查阶段
- [ ] Docstring 格式符合标准
- [ ] 中文文档完整（需求、设计、README）
- [ ] 无冗余或重复文件
- [ ] 提交消息符合 Conventional Commits
- [ ] 代码格式化和质量检查已通过

---

## 附加说明

- 本项目遵循 VibeCoding 单仓库结构
- 根级别 CLAUDE.md 包含跨项目指南
- 每个 Week 目录都是独立的，有自己的配置
- 优先显式而非隐式（Python 之禅）
- 首先为人类编写代码，其次为计算机
- 性能很重要，但可读性更重要（在证明必要时再优化）

**项目宪章**: 完整的治理原则和非妥协规则见 `.cursor/constitution.md`

---

**仓库根目录**: `~/Documents/VibeCoding`
**父级 CLAUDE.md**: `../CLAUDE.md`（仓库级指南）
**项目宪章**: `.cursor/constitution.md`（v1.1.0）
