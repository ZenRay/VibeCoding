# Data Model Requirements Quality Checklist

**Purpose**: 验证数据模型需求的完整性、清晰度和一致性  
**Created**: 2026-01-10  
**Feature**: 001-db-query-tool  
**Depth**: 标准 (~25 项)  
**Audience**: 规格编写者自查  
**Status**: ✅ 评审完成 - 通过率 93% (26/28) [修订后]  
**Reviewed**: 2026-01-10  
**Updated**: 2026-01-10 (根据评审结果更新 spec.md 和 data-model.md 后)

---

## 评审摘要

| 结果 | 数量 | 说明 |
|------|------|------|
| ✅ 通过 | 26 | 需求已明确定义 |
| 🟡 需改进 | 0 | 全部已修复 |
| 🔴 缺失 | 2 | 可接受的缺失（循环引用不适用于当前设计） |

---

## 实体定义完整性

- [x] **CHK001** - 所有关键实体是否在规格中明确定义？（数据库连接、元数据、查询、结果） [Completeness, Spec §Key Entities]
  > ✅ **通过** - Spec §Key Entities 定义了 4 个核心实体：数据库连接、数据库元数据、SQL 查询、查询结果

- [x] **CHK002** - 每个实体的必需字段和可选字段是否明确区分？ [Clarity, data-model.md]
  > ✅ **通过** - data-model.md 使用 `Field(...)` 和 `Field(None)` 明确区分必需和可选字段

- [x] **CHK003** - 实体字段的数据类型是否明确定义？（如 `port: int | None` vs `port: Optional[int]`） [Clarity, data-model.md §1.1]
  > ✅ **通过** - data-model.md 使用 Python 3.10+ 类型语法 `int | None`，类型定义清晰

- [x] **CHK004** - 实体的生命周期是否明确？（如查询历史仅当前会话，元数据持久化） [Completeness, Spec §FR-018]
  > ✅ **通过** - Spec 明确定义：
  > - 查询历史：仅当前会话（FR-018）
  > - 元数据：持久化缓存（FR-005, FR-006）
  > - 连接：持久化存储（FR-003）

- [x] **CHK005** - 是否定义了实体的唯一标识符策略？（如连接名称唯一、元数据按连接关联） [Completeness, data-model.md §2.1]
  > ✅ **通过** - data-model.md §2.1 定义：
  > - `name: Column(String(255), unique=True)`
  > - `connection_id: ForeignKey(..., unique=True)` 1:1 关系

---

## 字段约束与验证

- [x] **CHK006** - 字符串字段的长度限制是否明确？（如连接名称最大长度、SQL 查询最大长度） [Clarity, data-model.md §5.2]
  > ✅ **通过** - 定义了：
  > - 连接名称：255 字符（§2.1）
  > - SQL 查询：10000 字符（§5.2）
  > - api.yaml 限制连接名称 1-100 字符

- [x] **CHK007** - 必填字段与可空字段的定义是否一致？Pydantic 模型与 SQLAlchemy 模型是否对齐？ [Consistency, data-model.md]
  > ✅ **通过** - Pydantic 和 SQLAlchemy 模型字段定义一致：
  > - `host: str | None` ↔ `Column(String(255), nullable=True)`
  > - `port: int | None` ↔ `Column(Integer, nullable=True)`

- [x] **CHK008** - 枚举值是否完整定义？（如 `DatabaseType`、`QueryStatus`、`ErrorCode`） [Completeness, data-model.md §1.1, §1.3, §1.4]
  > ✅ **通过** - 定义了完整枚举：
  > - `DatabaseType`: POSTGRESQL, MYSQL, SQLITE
  > - `QueryStatus`: PENDING, EXECUTING, SUCCESS, FAILED, CANCELLED, TIMEOUT
  > - `ErrorCode`: 17 种错误代码

- [x] **CHK009** - 日期时间字段的格式和时区处理是否定义？（UTC vs 本地时间） [Gap]
  > ✅ **通过** [修订后] - FR-025 已补充："系统必须使用 UTC 时间存储所有日期时间字段"。data-model.md Overview 补充设计原则："所有日期时间字段使用 UTC 时间存储"

- [x] **CHK010** - 数值字段的范围约束是否定义？（如端口 1-65535、超时 1-30 秒） [Gap]
  > ✅ **通过** [修订后] - data-model.md §1.1 DatabaseConnectionResponse 补充 `port: Field(..., ge=1, le=65535)`。§5.2 补充 `PORT_RULES`

---

## 实体关系

- [x] **CHK011** - 实体之间的关系类型是否明确？（如 Connection ↔ MetadataCache 是 1:1） [Completeness, data-model.md §3]
  > ✅ **通过** - data-model.md §3 图示明确展示 1:1 关系

- [x] **CHK012** - 级联删除行为是否定义？删除连接时元数据缓存是否自动删除？ [Clarity, data-model.md §2.1]
  > ✅ **通过** - 定义了：
  > - `cascade="all, delete-orphan"` 在关系定义
  > - `ForeignKey(..., ondelete="CASCADE")` 在外键定义

- [x] **CHK013** - 关联实体的引用完整性是否保证？外键约束是否定义？ [Completeness, data-model.md §2.1]
  > ✅ **通过** - 定义了外键约束：`ForeignKey("database_connections.id", ondelete="CASCADE")`

- [ ] **CHK014** - 是否存在循环引用或孤儿记录的处理需求？ [Gap]
  > 🔴 **缺失** - 当前简单的 1:1 关系不存在循环引用风险。孤儿记录通过级联删除处理

---

## 状态转换

- [x] **CHK015** - 实体状态机是否完整定义？（如查询状态：PENDING → EXECUTING → SUCCESS/FAILED） [Completeness, data-model.md §4.1]
  > ✅ **通过** - data-model.md §4.1 提供了完整的状态机图

- [x] **CHK016** - 状态转换的触发条件是否明确？（如何从 EXECUTING 转到 CANCELLED） [Clarity, data-model.md §4.1]
  > ✅ **通过** - 状态机图标注了触发条件：`execute()`、`cancel()`、`timeout`、`success`、`error`

- [x] **CHK017** - 非法状态转换是否定义了错误处理？（如 SUCCESS 不能转回 EXECUTING） [Gap]
  > ✅ **通过** [修订后] - data-model.md §4.1 已补充："任何从终态（SUCCESS、FAILED、CANCELLED、TIMEOUT）的状态转换尝试都应被忽略并记录警告日志，不抛出异常"

- [x] **CHK018** - 并发状态变更的处理是否定义？（如同时取消和超时） [Gap]
  > ✅ **通过** [修订后] - data-model.md §4.1 已补充："当取消和超时同时发生时，优先处理先到达的事件。如果无法确定顺序，优先标记为 CANCELLED（用户主动操作优先）"

---

## 序列化与 API 契约

- [x] **CHK019** - API 请求/响应模型与内部模型的映射是否清晰？ [Clarity, data-model.md §1]
  > ✅ **通过** - data-model.md 明确分离 API 模型（§1 Pydantic）和存储模型（§2 SQLAlchemy）

- [x] **CHK020** - JSON 字段命名约定是否一致？（camelCase for API, snake_case for internal） [Consistency, data-model.md]
  > ✅ **通过** - 所有 Pydantic 模型配置 `alias_generator=to_camel`

- [x] **CHK021** - 可选字段在 API 响应中的表示是否定义？（null vs 省略） [Gap]
  > ✅ **通过** [修订后] - FR-026 已补充："API 响应中的可选字段为空时，必须返回 null 值而非省略该字段"。data-model.md Overview 设计原则也补充了此规则

- [x] **CHK022** - 列表响应的分页策略是否定义？（当前版本是否需要分页） [Gap]
  > ✅ **通过** - Spec Out of Scope 隐式说明当前版本简化设计，QueryResult 包含 `truncated` 字段表示结果被 LIMIT 截断

---

## 存储约束

- [x] **CHK023** - 存储容量限制是否与数据模型对齐？（100MB 总容量、5MB 单个元数据） [Consistency, Spec §FR-003, §Key Entities]
  > ✅ **通过** - 一致定义：
  > - 总容量：100MB（FR-003）
  > - 单个元数据：5MB（Key Entities）
  > - 内存缓存：50MB（FR-023）

- [x] **CHK024** - 索引策略是否支持常用查询模式？ [Completeness, data-model.md §6]
  > ✅ **通过** - 定义了关键索引：
  > - `idx_db_connections_name` (唯一)
  > - `idx_metadata_cache_connection`
  > - `idx_db_connections_type`
  > - `idx_metadata_cache_cached_at`

- [x] **CHK025** - 数据迁移策略是否定义？模型变更时如何处理现有数据？ [Gap]
  > ✅ **通过** [修订后] - FR-027 已补充："系统必须使用数据库迁移工具（如 Alembic）管理本地存储模式的版本变更"。data-model.md 新增 §7 "Data Migration Strategy" 详细说明迁移策略

---

## 边界情况

- [x] **CHK026** - 空值和默认值的处理是否一致？（如 `views: []` vs `views: null`） [Consistency]
  > ✅ **通过** - Pydantic 模型使用 `default_factory=list` 确保空列表而非 null

- [x] **CHK027** - 特殊数据类型的序列化是否定义？（如 BLOB 显示为 `[BINARY]`） [Completeness, Spec §FR-011]
  > ✅ **通过** - FR-011 定义：BLOB 显示为 `[BINARY]`，JSON/XML 显示为格式化文本

- [x] **CHK028** - 超大 JSON 字段的处理是否定义？（元数据 JSON 可能很大） [Gap]
  > ✅ **通过** - 通过 5MB 单个元数据限制（Key Entities）和 50MB 内存缓存限制（FR-023）间接处理

---

## Summary

| 维度 | 项目数 | ✅ 通过 | 🟡 需改进 | 🔴 缺失 |
|------|--------|---------|-----------|---------|
| 实体定义完整性 | 5 | 5 | 0 | 0 |
| 字段约束与验证 | 5 | 5 | 0 | 0 |
| 实体关系 | 4 | 3 | 0 | 1 |
| 状态转换 | 4 | 4 | 0 | 0 |
| 序列化与 API 契约 | 4 | 4 | 0 | 0 |
| 存储约束 | 3 | 3 | 0 | 0 |
| 边界情况 | 3 | 3 | 0 | 0 |
| **总计** | **28** | **26** | **0** | **2** |

---

## 评审结论

### 通过率: 93% (26/28) [修订后提升]

### 修订内容 (2026-01-10)

以下项目已通过更新 `spec.md` 和 `data-model.md` 解决：

| 项目 | 修订内容 |
|------|----------|
| CHK009 | FR-025 补充 UTC 时间策略，data-model.md 补充设计原则 |
| CHK010 | data-model.md 补充端口范围验证和 PORT_RULES |
| CHK017 | data-model.md §4.1 补充非法状态转换处理规则 |
| CHK018 | data-model.md §4.1 补充并发状态变更优先级 |
| CHK021 | FR-026 补充 null 字段返回策略 |
| CHK025 | FR-027 补充迁移策略，data-model.md 新增 §7 |

### 重要发现

**✅ 优势领域**:
1. 实体定义完整，字段类型清晰
2. 实体关系和级联行为定义完善
3. JSON 序列化约定一致（camelCase）
4. 存储约束与数据模型对齐
5. 边界情况处理完善
6. UTC 时间策略明确
7. 状态转换规则完善
8. 数据迁移策略已定义

**🔴 可接受的缺失** (2 项):
1. CHK014 - 循环引用处理：当前 1:1 简单关系不存在此问题
2. CHK014 已在原评审中标记为可忽略

---

**评审者备注**: 数据模型设计质量优秀，所有关键需求已明确定义。可以进入开发阶段。
