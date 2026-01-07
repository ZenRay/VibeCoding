# 经验教训和最佳实践

**文档版本**: v1.0  
**创建时间**: 2026-01-08  
**最后更新**: 2026-01-08

## 📋 目录

1. [核心教训](#核心教训)
2. [技术决策](#技术决策)
3. [避坑指南](#避坑指南)
4. [可复用方案](#可复用方案)

---

## 核心教训

### 教训 1：环境一致性至关重要 ⭐⭐⭐⭐⭐

**问题**：
- 本地 Node v12，CI 使用 Node 20
- 本地 Python 版本不确定，CI 使用 Python 3.12
- 导致：Prettier 无法运行，格式化失败

**解决方案**：
```bash
# 统一使用 Docker 开发
cd env && ./start.sh
cd env && ./check-running.sh  # 在 Docker 中检查
```

**教训**：
> **本地开发环境必须与 CI 环境一致，否则会出现大量环境问题。**

**最佳实践**：
- ✅ 使用 Docker 开发（环境 100% 一致）
- ✅ 使用 `.nvmrc` 和 `.python-version` 声明版本
- ✅ CI 也使用 Docker 执行检查

---

### 教训 2：业务逻辑不应依赖数据库特性 ⭐⭐⭐⭐⭐

**问题**：
- 标签名称自动转大写依赖 PostgreSQL 触发器
- SQLite 测试环境没有触发器
- 导致：测试失败 `assert 'api_test' == 'API_TEST'`

**解决方案**：
```python
# 在 Service 层处理业务规则
@staticmethod
def _normalize_tag_name(name: str) -> str:
    """应用层面处理，数据库无关"""
    return "".join(
        c.upper() if c.isascii() and c.isalpha() else c 
        for c in name.strip()
    )
```

**教训**：
> **业务逻辑应该在应用层实现，不依赖特定数据库的特性。**

**最佳实践**：
- ✅ 在 Service 层处理业务规则
- ✅ 数据库只负责存储和基本约束
- ✅ 测试环境可以使用不同数据库

---

### 教训 3：SQLAlchemy 模型必须显式导入 ⭐⭐⭐⭐⭐

**问题**：
- `conftest.py` 只导入了 `Base`
- `Base.metadata.create_all()` 时 metadata 为空
- 导致：`no such table: tags/tickets`

**解决方案**：
```python
# tests/conftest.py
from app.database import Base
from app.models import Tag, Ticket, TicketTag  # 必须导入！

@pytest.fixture
def db():
    Base.metadata.create_all(bind=engine)  # 现在会创建表
```

**教训**：
> **SQLAlchemy 的 declarative_base() 只有在模型被导入后，才会将它们注册到 Base.metadata。**

**最佳实践**：
- ✅ 在测试配置中显式导入所有模型
- ✅ 在 `app/models/__init__.py` 中导出所有模型
- ✅ 使用 `# noqa: F401` 避免 "unused import" 警告

---

### 教训 4：SQLite 内存数据库的连接陷阱 ⭐⭐⭐⭐

**问题**：
- 使用 `sqlite:///:memory:`
- 每个连接创建新的内存数据库
- `db` fixture 和 `client` fixture 看到不同的数据库

**解决方案**：
```python
# 使用文件数据库
import tempfile
import os

_temp_db_path = os.path.join(tempfile.gettempdir(), "test_ticket_db.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{_temp_db_path}"
```

**教训**：
> **SQLite 内存数据库每个连接独立，不适合多连接测试场景。**

**最佳实践**：
- ✅ 测试使用文件数据库
- ✅ 每个测试后清理数据而不是删除表
- ✅ 使用 autouse fixture 确保表创建

---

### 教训 5：不要手动调整格式化工具的输出 ⭐⭐⭐⭐

**问题**：
- 手动将 `str | None` 拆分成多行
- Black 期望单行格式
- 导致：pre-commit 反复失败

**解决方案**：
```python
# ✅ 让 Black 自动处理
status: str | None = Query(...)

# ❌ 不要手动拆分
status: str
| None = Query(...)
```

**教训**：
> **格式化工具的输出不应该手动调整，让工具自己处理。**

**最佳实践**：
- ✅ 运行格式化工具后不再手动编辑
- ✅ 如果格式不满意，调整工具配置
- ✅ 团队统一使用相同的格式化配置

---

## 技术决策

### 为什么选择 Docker

**对比分析**：

| 方面 | 本地开发 | Docker 开发 |
|------|---------|------------|
| 环境配置 | 需要安装多个工具 | 一键启动 |
| 环境一致性 | 可能不同 | 100% 一致 |
| 团队协作 | 环境差异 | 完全相同 |
| CI/CD | 可能不一致 | 完全一致 |
| 依赖隔离 | 可能冲突 | 完全隔离 |

**决策**：使用 Docker，收益远大于成本

### 为什么选择 SQLite 测试

**对比分析**：

| 方面 | PostgreSQL 测试 | SQLite 测试 |
|------|----------------|------------|
| 速度 | 较慢 | 快 |
| 环境依赖 | 需要数据库服务 | 无需额外服务 |
| CI 成本 | 需要启动服务 | 零成本 |
| 功能差异 | 无 | 有（触发器等） |

**决策**：使用 SQLite 测试，但业务逻辑保持数据库无关

### 为什么选择 Zustand

**对比分析**：

| 方面 | Redux | Zustand | Context API |
|------|-------|---------|------------|
| 学习曲线 | 陡峭 | 平缓 | 简单 |
| 模板代码 | 多 | 少 | 中等 |
| 性能 | 好 | 好 | 一般 |
| 中间件 | 丰富 | 足够 | 需自己实现 |

**决策**：Zustand - 简单够用，性能好

---

## 避坑指南

### 坑 1：Pre-commit Hooks 失败不提交

**现象**：
```bash
git commit -m "..."
# pre-commit hook 失败，提交被阻止
```

**解决**：
```bash
# 方案 1：修复问题后重新提交
cd env && ./check-running.sh  # 自动修复
git add -A && git commit -m "..."

# 方案 2：跳过 hooks（紧急情况）
git commit -m "..." --no-verify
```

### 坑 2：GitHub Actions 无法推送

**现象**：
```
remote: Permission to repo.git denied to github-actions[bot]
```

**原因**：
- Actions bot 没有推送到 main 分支的权限
- 这是 GitHub 的安全机制

**解决**：
```yaml
# 不要让 Actions 自动推送修复
# 而是提示用户在本地修复
- name: Check format
  run: |
    if ! prettier --check "src/**/*.{ts,tsx,css}"; then
      echo "请在本地运行: cd env && ./check-running.sh"
      exit 1
    fi
```

### 坑 3：Volume 挂载覆盖依赖

**现象**：
```
后端：.venv 被覆盖，依赖消失
前端：node_modules 被覆盖，依赖消失
```

**解决**：
```yaml
# 使用 named volume 持久化依赖
services:
  backend:
    volumes:
      - ../backend:/app
      - backend_venv:/app/.venv      # 持久化
  
  frontend:
    volumes:
      - ../frontend:/app
      - frontend_node_modules:/app/node_modules  # 持久化
```

### 坑 4：热重载不工作

**可能原因**：
1. Volume 挂载不正确
2. 服务命令缺少 `--reload` 参数
3. 文件系统通知不工作

**解决**：
```yaml
# 确保命令包含热重载参数
services:
  backend:
    command: .venv/bin/uvicorn app.main:app --reload  # ✅
  
  frontend:
    command: npm run dev -- --host 0.0.0.0  # ✅ Vite 默认热重载
```

---

## 可复用方案

### 方案 1：Docker 开发环境模板

```yaml
# docker-compose.yml 模板
version: '3.8'

services:
  backend:
    build:
      context: ../backend
      dockerfile: ../env/Dockerfile.backend
    volumes:
      - ../backend:/app              # 代码挂载
      - backend_deps:/app/.venv      # 依赖持久化
    command: <热重载命令>
  
  frontend:
    build:
      context: ../frontend
      dockerfile: ../env/Dockerfile.frontend
    volumes:
      - ../frontend:/app                # 代码挂载
      - frontend_deps:/app/node_modules # 依赖持久化
    command: <热重载命令>

volumes:
  backend_deps:
  frontend_deps:
```

### 方案 2：测试数据库配置模板

```python
# tests/conftest.py 模板
import os
import tempfile
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 导入所有模型（关键！）
from app.models import *  # 或显式导入

# 使用文件数据库
_temp_db_path = os.path.join(tempfile.gettempdir(), "test_db.db")
if os.path.exists(_temp_db_path):
    os.remove(_temp_db_path)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{_temp_db_path}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, 
                      connect_args={"check_same_thread": False})

@pytest.fixture(scope="function", autouse=True)
def setup_database():
    """确保表创建"""
    Base.metadata.create_all(bind=engine)
    yield
    # 清理数据
    with engine.connect() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.commit()
```

### 方案 3：CI 配置模板（Docker 方式）

```yaml
# .github/workflows/ci.yml 模板
jobs:
  backend-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Run checks in Docker
        run: |
          docker run --rm \
            -v "${{ github.workspace }}/backend:/app" \
            -w /app \
            python:3.12-slim \
            bash -c "
              pip install -q -e '.[dev]' && 
              black --check . && 
              isort --check-only . && 
              ruff check . && 
              pytest --cov=app
            "
```

### 方案 4：代码检查脚本模板

```bash
#!/bin/bash
# check.sh 模板

# 后端检查
docker run --rm -v "$(pwd)/backend:/app" -w /app python:3.12-slim bash -c "
    pip install -q black isort ruff pytest &&
    black --check . || (black . && echo '已修复格式') &&
    isort --check-only . || (isort . && echo '已修复导入') &&
    ruff check . || (ruff check --fix . && echo '已修复代码') &&
    pytest
"

# 前端检查
docker run --rm -v "$(pwd)/frontend:/app" -w /app node:20-alpine sh -c "
    npm install &&
    npx prettier --check 'src/**/*.{ts,tsx,css}' || 
    (npx prettier --write 'src/**/*.{ts,tsx,css}' && echo '已修复格式') &&
    npm run lint &&
    npm run type-check
"
```

---

## 避坑指南

### 后端开发

✅ **DO（应该做）**
- 在 Service 层处理业务逻辑
- 使用类型注解（`str | None`）
- 导入所有模型到测试配置
- 使用文件数据库测试
- 让 Black 自动处理格式

❌ **DON'T（不要做）**
- 依赖数据库触发器处理业务逻辑
- 手动拆分类型注解为多行
- 忘记导入模型导致表创建失败
- 使用 SQLite 内存数据库（多连接场景）
- 手动调整 Black 格式化的输出

### 前端开发

✅ **DO（应该做）**
- 使用 Prettier 自动格式化
- 箭头函数简化：`arr.map(x => x * 2)`
- JSX 属性使用单引号
- 组件拆分，保持简单
- 使用 TypeScript 严格模式

❌ **DON'T（不要做）**
- 混用单引号和双引号
- 一个文件导出多个非组件内容（React Fast Refresh 警告）
- 忘记添加 `key` prop
- 过度优化（过早使用 memo/useCallback）
- 忽略 TypeScript 错误

### Docker 开发

✅ **DO（应该做）**
- 使用 named volume 持久化依赖
- 使用 bind mount 实时同步代码
- 配置热重载
- 使用国内镜像加速
- 定期清理未使用的镜像和 volume

❌ **DON'T（不要做）**
- 在宿主机安装开发工具
- 忽略 volume 挂载配置
- 忘记添加健康检查
- 使用 `latest` 标签（应该固定版本）
- 在 Dockerfile 中安装不必要的工具

---

## 可复用代码片段

### Service 层模板

```python
class ExampleService:
    """业务逻辑服务类"""
    
    @staticmethod
    def get_list(db: Session, filters: dict) -> list[Model]:
        """获取列表，支持过滤"""
        query = db.query(Model)
        
        if filters.get('status'):
            query = query.filter(Model.status == filters['status'])
        
        return query.all()
    
    @staticmethod
    def get_by_id(db: Session, id: int) -> Model:
        """根据 ID 获取"""
        obj = db.query(Model).filter(Model.id == id).first()
        if not obj:
            raise NotFoundError(f"ID {id} 不存在")
        return obj
    
    @staticmethod
    def create(db: Session, data: CreateSchema) -> Model:
        """创建"""
        obj = Model(**data.model_dump())
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    
    @staticmethod
    def update(db: Session, id: int, data: UpdateSchema) -> Model:
        """更新"""
        obj = ExampleService.get_by_id(db, id)
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)
        db.commit()
        db.refresh(obj)
        return obj
    
    @staticmethod
    def delete(db: Session, id: int) -> None:
        """删除"""
        obj = ExampleService.get_by_id(db, id)
        db.delete(obj)
        db.commit()
```

### React Hook 模板

```typescript
export function useData(params?: QueryParams) {
  const [data, setData] = useState<Data[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  
  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await service.getData(params)
      setData(response.data)
    } catch (err) {
      setError(err as Error)
    } finally {
      setLoading(false)
    }
  }, [params])
  
  useEffect(() => {
    fetchData()
  }, [fetchData])
  
  return { data, loading, error, refetch: fetchData }
}
```

---

## 检查清单

### 提交前检查清单

- [ ] 在 Docker 中运行检查：`cd env && ./check-running.sh`
- [ ] 后端格式化通过（Black、isort）
- [ ] 后端代码检查通过（Ruff）
- [ ] 后端测试通过（pytest）
- [ ] 前端格式化通过（Prettier）
- [ ] 前端代码检查通过（ESLint）
- [ ] 前端类型检查通过（TypeScript）
- [ ] 前端构建通过（Vite build）

### 代码审查检查清单

**后端**：
- [ ] 业务逻辑在 Service 层
- [ ] 不依赖数据库特性
- [ ] 类型注解正确
- [ ] 测试覆盖关键路径
- [ ] 错误处理完善

**前端**：
- [ ] 组件职责单一
- [ ] Props 有类型定义
- [ ] 副作用使用 useEffect
- [ ] 列表有 key prop
- [ ] 样式使用 Tailwind

---

## 关键数字

### 开发统计

- **总提交数**：100+
- **修复问题**：4 个核心问题
- **创建文档**：14 个 specs 文档
- **代码覆盖率**：82%+
- **测试用例**：35 个

### 时间投入

- **环境配置**：2 天
- **后端开发**：3 天
- **前端开发**：4 天
- **问题修复**：1 天
- **文档整理**：1 天
- **总计**：约 11 天

### 经验值

- **Docker 节省时间**：80%（环境配置）
- **自动化测试节省时间**：60%（手动测试）
- **代码质量工具节省时间**：40%（格式调整）
- **问题修复时间**：30%（因环境不一致）

---

## 总结

### 核心经验

1. **环境一致性是王道** - Docker 解决 95% 问题
2. **业务逻辑独立** - 不依赖数据库特性
3. **自动化优先** - 让工具自动修复，不手动调整
4. **提交前检查** - 在 Docker 中检查，本地通过 = CI 通过

### 给未来项目的建议

1. **从第一天就使用 Docker** - 不要等出问题再迁移
2. **从第一天就配置 CI** - 自动化质量保证
3. **从第一天就写测试** - 避免后期补测试
4. **从第一天就写文档** - 知识沉淀和团队协作

### 可复用资产

本项目中可以直接复用到其他项目的：

- ✅ Docker 配置（docker-compose.yml, Dockerfile）
- ✅ CI 配置（.github/workflows/ci.yml）
- ✅ 代码质量配置（.pre-commit-config.yaml, pyproject.toml, .prettierrc）
- ✅ 测试配置（conftest.py）
- ✅ 检查脚本（env/check*.sh）

**这些配置和脚本可以作为模板，用于任何 FastAPI + React 项目！** 🎉
