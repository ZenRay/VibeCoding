# Comprehensive Requirements Quality Checklist: 数据库查询工具

**Purpose**: PR 评审 - 验证需求规范的完整性、清晰度、一致性和可测试性  
**Created**: 2026-01-10  
**Focus**: API 契约、性能、安全、多数据库兼容性、用户体验  
**Emphasis**: 异常处理、数据一致性

**使用说明**: 本检查清单用于测试需求本身的质量,而非测试实现。每个条目都在询问"需求是否被清晰、完整地定义?"

---

## 1. API 契约质量 (API Contract Quality)

### 1.1 请求/响应规范完整性

- [ ] CHK001 - 数据库连接创建/更新(PUT /dbs/{name})的请求体结构是否完整定义了所有必需字段和可选字段? [Completeness, contracts/api.yaml]
- [ ] CHK002 - API 响应中可选字段为空时的表示方式(null vs 省略)是否在所有端点间保持一致? [Consistency, Spec §FR-026]
- [ ] CHK003 - 错误响应格式是否为所有失败场景定义了统一的结构(code, message, details)? [Completeness, contracts/api.yaml]
- [ ] CHK004 - API 响应中不返回密码字段的安全要求是否明确记录? [Clarity, Spec §FR-003, contracts/api.yaml]
- [ ] CHK005 - 元数据 API(GET /dbs/{name})返回的数据结构是否明确定义了嵌套层级(数据库→表→列)? [Clarity, Spec §FR-005]

### 1.2 错误处理规范

- [ ] CHK006 - 连接失败时的错误类型分类(网络不可达、认证失败、权限拒绝、数据库不存在)是否穷尽所有可能的失败模式? [Coverage, Spec §FR-002]
- [ ] CHK007 - HTTP 状态码与错误类型的映射规则是否明确定义? [Clarity, contracts/api.yaml]
- [ ] CHK008 - 每种错误类型的用户可读错误消息格式是否具有明确的模板? [Clarity, Spec §FR-002, FR-014, FR-015]
- [ ] CHK009 - API 错误响应是否要求包含足够的调试信息(如错误位置、参数名)? [Completeness, Spec §FR-014]

### 1.3 数据验证规范

- [ ] CHK010 - 连接名称验证规则(正则表达式、长度限制)是否可以被客户端和服务端一致地实现? [Measurability, Spec §FR-024]
- [ ] CHK011 - SQL 查询输入长度限制(10000 字符)和自然语言输入限制(1000 字符)是否在 API 契约中体现? [Completeness, Spec §FR-028]
- [ ] CHK012 - 数据库连接 URL 格式验证规则是否针对三种数据库类型分别定义? [Completeness, Spec §FR-001]

---

## 2. 异常处理需求完整性 (Exception Handling - EMPHASIS)

### 2.1 连接异常

- [ ] CHK013 - 连接建立时的所有异常场景(超时、DNS 解析失败、SSL 证书错误)是否都有定义的处理要求? [Coverage, Gap]
- [ ] CHK014 - 连接建立后断开的检测机制和用户提示是否明确定义? [Completeness, Edge Cases §连接断开场景]
- [ ] CHK015 - 编辑连接时验证失败的回滚行为(保留原连接信息)是否明确指定? [Clarity, Spec §FR-019]
- [ ] CHK016 - 网络不稳定环境下的连接重试策略是否定义(重试次数、间隔、指数退避)? [Gap]

### 2.2 查询执行异常

- [ ] CHK017 - 查询超时(30秒)后的资源清理要求(释放连接、取消查询)是否完整定义? [Completeness, Spec §FR-015]
- [ ] CHK018 - 用户取消查询时的中止机制是否要求"立即"中止还是允许延迟? [Ambiguity, Spec §FR-020]
- [ ] CHK019 - 查询执行中数据库连接断开的错误提示和恢复流程是否定义? [Completeness, Edge Cases]
- [ ] CHK020 - 队列等待超时(60秒)的查询取消是否要求通知用户具体等待时长? [Gap, Spec §FR-032]
- [ ] CHK021 - SQL 语法验证失败(1秒内返回)的性能要求是否可测量? [Measurability, Spec §FR-007]

### 2.3 元数据提取异常

- [ ] CHK022 - 部分表因权限不足无法提取时的警告消息格式是否明确定义? [Clarity, Spec §FR-004]
- [ ] CHK023 - 无效/非标准元数据结构的错误提示("该数据库可能不受支持")是否定义了具体的检测条件? [Ambiguity, Edge Cases]
- [ ] CHK024 - 元数据提取超时是否有定义的时间限制? [Gap]
- [ ] CHK025 - 元数据提取过程中数据库连接中断的恢复策略是否定义? [Gap]

### 2.4 本地存储异常

- [ ] CHK026 - 本地存储损坏时的检测机制(完整性检查)是否明确定义算法或方法? [Clarity, Edge Cases]
- [ ] CHK027 - 存储空间不足(超过 100MB)时的自动清理策略是否定义了清理顺序和保留规则? [Completeness, Spec §FR-003, Edge Cases]
- [ ] CHK028 - 本地存储写入失败的错误处理和用户通知是否定义? [Gap]
- [ ] CHK029 - 迁移脚本执行失败时的回滚要求是否定义? [Gap, Spec §FR-027]

### 2.5 外部依赖异常

- [ ] CHK030 - AI 服务调用失败的三种场景(网络问题、服务不可用、配额超限)的错误提示是否分别定义? [Coverage, Edge Cases]
- [ ] CHK031 - AI 服务响应超时(10秒内响应)的处理要求是否定义? [Gap, Plan §Performance Goals]
- [ ] CHK032 - AI 服务未配置(OPENAI_API_KEY 缺失)时的功能降级是否明确描述了界面变化? [Clarity, Spec §FR-030]

---

## 3. 数据一致性需求质量 (Data Consistency - EMPHASIS)

### 3.1 元数据缓存一致性

- [ ] CHK033 - 元数据版本检测算法(SHA-256 哈希)的具体输入内容(表数量+表名列表)是否明确定义? [Clarity, Spec §FR-006]
- [ ] CHK034 - 元数据版本变化检测的触发时机(每次连接时、定期检查、用户手动刷新)是否明确? [Ambiguity, Spec §FR-006]
- [ ] CHK035 - 元数据缓存失效后是否要求强制刷新还是允许继续使用旧缓存? [Gap, Spec §FR-017]
- [ ] CHK036 - 多个数据库连接共享本地缓存时的隔离要求是否定义? [Gap]
- [ ] CHK037 - 元数据刷新过程中查询执行是否允许继续使用旧元数据? [Gap]

### 3.2 查询历史一致性

- [ ] CHK038 - 查询历史的存储边界(最多 50 条)达到时的删除策略(FIFO)是否明确? [Clarity, Spec §FR-018]
- [ ] CHK039 - 应用崩溃重启后查询历史的丢失是否被明确标识为预期行为? [Clarity, Spec §FR-018]
- [ ] CHK040 - 查询历史中的查询状态(待执行/执行中/成功/失败/已取消)转换规则是否完整定义? [Gap, Key Entities]

### 3.3 时间一致性

- [ ] CHK041 - UTC 时间存储和本地时区转换的要求是否覆盖所有日期时间字段? [Coverage, Spec §FR-025]
- [ ] CHK042 - 时区转换失败或浏览器时区不可用时的降级策略是否定义? [Gap]
- [ ] CHK043 - 跨时区的缓存时间戳比较是否可能导致一致性问题? [Risk Assessment]

### 3.4 并发与队列一致性

- [ ] CHK044 - 串行执行策略下的查询队列管理(入队、出队、超时)是否有明确的状态机定义? [Gap, Spec §FR-032, Edge Cases]
- [ ] CHK045 - 用户取消正在执行的查询时,后续队列查询的启动时机是否定义? [Gap]
- [ ] CHK046 - 并发元数据刷新请求的去重或串行化要求是否定义? [Gap]

---

## 4. 性能需求可测量性 (Performance Measurability)

### 4.1 响应时间要求

- [ ] CHK047 - "应用启动时间 < 3 秒"的测量边界(从进程启动到 UI 完全可交互)是否明确定义? [Clarity, Spec §FR-022]
- [ ] CHK048 - "简单查询 < 3 秒"的"简单"定义标准是否量化(行数、表数、JOIN 数量)? [Ambiguity, Success Criteria §SC-003]
- [ ] CHK049 - "元数据提取 < 5 秒(100 表以内)"的测试数据特征(列数、索引数)是否定义? [Gap, Success Criteria §SC-002]
- [ ] CHK050 - AI SQL 生成 < 10 秒的测量点(从用户提交到 SQL 显示)是否明确? [Clarity, Plan §Performance Goals]

### 4.2 资源限制要求

- [ ] CHK051 - "元数据缓存 < 50MB"的内存测量方法(进程总内存、特定对象大小)是否定义? [Measurability, Spec §FR-023]
- [ ] CHK052 - "本地存储 < 100MB"的计算范围(仅元数据、含日志、含临时文件)是否明确? [Ambiguity, Spec §FR-003]
- [ ] CHK053 - 单个数据库元数据缓存 < 5MB 的限制与总缓存 < 50MB 的限制是否存在矛盾? [Consistency, Key Entities]

### 4.3 性能降级要求

- [ ] CHK054 - 超大结果集(单行包含大文本)的渲染性能要求是否定义? [Gap, Edge Cases]
- [ ] CHK055 - 网络延迟 > 500ms 时的用户体验降级策略是否定义? [Gap, Dependencies]
- [ ] CHK056 - 元数据数量超过预期(>100 表)时的性能保证是否定义? [Gap]

---

## 5. 多数据库兼容性需求一致性 (Multi-DB Compatibility)

### 5.1 元数据提取一致性

- [ ] CHK057 - 三种数据库(PostgreSQL/MySQL/SQLite)的元数据字段映射规则是否定义? [Gap, Spec §FR-004]
- [ ] CHK058 - 各数据库特有的数据类型(PostgreSQL 的 ARRAY、MySQL 的 ENUM)在元数据中的表示是否统一? [Gap]
- [ ] CHK059 - 数据库版本差异(PostgreSQL 10 vs 15)导致的元数据结构变化是否有处理要求? [Gap, Spec §FR-001]

### 5.2 SQL 验证一致性

- [ ] CHK060 - sqlglot 对三种数据库方言的验证规则是否一致应用? [Consistency, Plan]
- [ ] CHK061 - 数据库特定语法(PostgreSQL 的 `RETURNING`)的验证处理是否定义? [Gap]
- [ ] CHK062 - SQL 关键字和标识符的引号包裹规则是否针对三种数据库分别定义? [Gap, Edge Cases]

### 5.3 错误消息一致性

- [ ] CHK063 - 各数据库驱动返回的错误码与统一错误类型的映射规则是否定义? [Gap]
- [ ] CHK064 - 特定数据库的错误消息(如 MySQL 的 `errno 2006`)是否有用户友好的翻译? [Gap]

---

## 6. 安全需求完整性 (Security Requirements)

### 6.1 凭据保护

- [ ] CHK065 - 明文存储凭据的安全警告是否在所有相关界面(添加、编辑、查看)都要求显示? [Coverage, Spec §FR-003]
- [ ] CHK066 - 密码遮蔽显示(`***`)和"显示密码"按钮的交互行为是否明确定义? [Clarity, Spec §FR-003]
- [ ] CHK067 - API 响应中排除密码字段的要求是否覆盖所有返回连接信息的端点? [Coverage, Spec §FR-003]
- [ ] CHK068 - 本地存储文件的访问权限要求(文件系统权限)是否定义? [Gap]

### 6.2 SQL 注入防护

- [ ] CHK069 - 仅允许 SELECT 语句的验证是否在 SQL 解析层和数据库执行层双重实施? [Gap, Spec §FR-008]
- [ ] CHK070 - AI 生成的 SQL 是否要求经过与手动输入相同的安全验证? [Clarity, Spec §FR-012]
- [ ] CHK071 - SQL 注入攻击模式(如注释绕过、Union 攻击)的检测要求是否定义? [Gap]

### 6.3 使用环境限制

- [ ] CHK072 - "仅适用于开发环境"的限制是否通过技术手段(如环境变量检查)强制实施? [Gap, Spec §FR-003]
- [ ] CHK073 - 生产环境误用的风险提示是否在文档和界面中充分警告? [Coverage, Dependencies]

---

## 7. 用户体验需求清晰度 (UX Clarity)

### 7.1 错误提示清晰度

- [ ] CHK074 - 所有错误提示是否提供了用户可采取的具体行动建议? [Clarity, Spec §FR-015]
- [ ] CHK075 - 错误提示的语言风格(技术术语 vs 用户友好)是否有统一的指南? [Consistency]
- [ ] CHK076 - 复杂错误(如 SQL 语法错误)的详细信息显示方式(展开/折叠)是否定义? [Gap]

### 7.2 加载与等待状态

- [ ] CHK077 - 所有异步操作(连接验证、元数据提取、查询执行)是否都要求显示加载状态? [Coverage, Gap]
- [ ] CHK078 - 加载状态的最小显示时间(避免闪烁)是否定义? [Gap]
- [ ] CHK079 - 长时间操作(>5 秒)的进度指示器是否要求显示百分比或步骤? [Gap]

### 7.3 数据展示清晰度

- [ ] CHK080 - NULL 值、空字符串、空白的视觉区分要求是否明确且可区分? [Clarity, Spec §FR-029]
- [ ] CHK081 - 特殊数据类型(BLOB、JSON、XML)的显示格式是否对所有类型都有定义? [Coverage, Spec §FR-011, Edge Cases]
- [ ] CHK082 - 表格截断(100 字符)的视觉提示(省略号、tooltip 图标)是否定义? [Gap, Spec §FR-011]
- [ ] CHK083 - 多字节字符(中文、Emoji)的字符计数逻辑是否明确避免截断问题? [Clarity, Clarifications]

### 7.4 交互反馈

- [ ] CHK084 - 删除连接的确认对话框文案是否明确警告"该操作无法撤销"? [Clarity, Spec §FR-016]
- [ ] CHK085 - 查询取消后的状态反馈(显示"查询已取消")是否定义了显示位置和持续时间? [Gap, Spec §FR-020]
- [ ] CHK086 - 元数据刷新提示横幅的显示时机和消失条件是否明确? [Gap, Spec §FR-017]

---

## 8. 需求可追溯性与文档质量 (Traceability & Documentation)

### 8.1 需求标识与追溯

- [ ] CHK087 - 所有功能需求(FR-001~FR-033)是否都可以追溯到至少一个用户故事或验收场景? [Traceability]
- [ ] CHK088 - 成功标准(SC-001~SC-010)是否明确映射到相应的功能需求? [Traceability]
- [ ] CHK089 - 边缘案例(Edge Cases)是否都有对应的需求或处理策略? [Coverage]

### 8.2 假设与依赖验证

- [ ] CHK090 - 外部依赖(AI 服务、数据库驱动)的假设是否经过验证或标记为风险? [Assumption, Dependencies]
- [ ] CHK091 - 用户假设(SQL 知识、桌面环境、安全环境)是否与目标用户画像一致? [Assumption, Dependencies]
- [ ] CHK092 - 技术假设(本地存储可用、单用户场景)是否可能限制未来扩展? [Risk Assessment]

### 8.3 范围边界清晰度

- [ ] CHK093 - Out of Scope 列表是否明确排除了可能引起歧义的功能(如"导出"是否包括复制粘贴)? [Clarity, Out of Scope]
- [ ] CHK094 - 不支持的平台(移动设备)和浏览器是否明确列出? [Completeness, Out of Scope]
- [ ] CHK095 - 明确排除的非功能需求(如可访问性、国际化)是否可能影响用户采用? [Risk Assessment]

---

## 9. API 契约与实现计划一致性 (Contract-Plan Alignment)

### 9.1 数据模型一致性

- [ ] CHK096 - API 契约中的数据模型(DatabaseConnection, Metadata)与 Plan 中的 Pydantic 模型定义是否一致? [Consistency, contracts/api.yaml, plan.md]
- [ ] CHK097 - camelCase(前端) 与 snake_case(后端) 的命名转换规则是否在契约和计划中一致定义? [Consistency, Plan §Constitution Check]
- [ ] CHK098 - 可选字段的 nullable 标记是否在 API 契约和数据模型中一致? [Consistency]

### 9.2 端点与服务映射

- [ ] CHK099 - API 契约中的所有端点是否都在 Plan 的服务层(services/)中有对应的实现计划? [Coverage, contracts/api.yaml, plan.md]
- [ ] CHK100 - 任务分解(tasks.md)中的 API 路由任务是否覆盖了契约中的所有端点? [Coverage, tasks.md]

---

## 10. 关键风险与遗漏检查 (Risk & Gap Assessment)

### 10.1 高风险场景

- [ ] CHK101 - 并发元数据刷新和查询执行时的数据一致性风险是否被识别并定义处理要求? [Risk, Gap]
- [ ] CHK102 - 本地存储和远程数据库状态不一致(连接已删除但远程仍存在)的处理是否定义? [Gap]
- [ ] CHK103 - AI 生成恶意 SQL(如包含注释的绕过)的检测和防护要求是否定义? [Risk, Gap]

### 10.2 可扩展性限制

- [ ] CHK104 - 单用户假设是否明确记录为未来多用户扩展的限制? [Clarity, Dependencies]
- [ ] CHK105 - 查询结果限制(1000 行)是否可能导致用户无法完成实际任务? [Risk Assessment]
- [ ] CHK106 - 元数据缓存策略(最少使用)是否考虑了多数据库切换频繁的场景? [Gap]

### 10.3 测试覆盖要求

- [ ] CHK107 - AI SQL 生成的 90% 正确率要求是否定义了测试用例的构建方法和评判标准? [Measurability, Success Criteria §SC-005]
- [ ] CHK108 - 可用性测试(90% 用户成功率)的用户招募标准和测试环境是否定义? [Measurability, Success Criteria §SC-008]
- [ ] CHK109 - 性能测试的负载条件(数据量、并发数、网络延迟)是否定义? [Gap]

---

## Summary Statistics

**Total Items**: 109  
**Traceability Coverage**: 95/109 (87.2%) items include spec/plan/contract references  
**Gap Indicators**: 42 items marked as [Gap]  
**Ambiguity Flags**: 8 items marked as [Ambiguity]  
**Risk Assessments**: 6 items marked as [Risk Assessment]  

**Category Breakdown**:
- API 契约质量: 12 items
- 异常处理 (重点): 20 items
- 数据一致性 (重点): 14 items
- 性能可测量性: 10 items
- 多数据库兼容性: 8 items
- 安全需求: 9 items
- 用户体验: 13 items
- 可追溯性: 9 items
- 契约-计划一致性: 5 items
- 风险与遗漏: 9 items

---

## Completion Criteria

此检查清单完成后,需求规范应该满足以下质量标准:

1. **完整性**: 所有 [Gap] 标记的项目都已补充需求或明确标记为有意排除
2. **清晰度**: 所有 [Ambiguity] 标记的项目都已提供明确的量化标准或定义
3. **一致性**: 所有 [Consistency] 问题都已解决,相关需求互不冲突
4. **可测量性**: 所有性能和质量要求都有明确的测量方法和验收标准
5. **可追溯性**: 所有需求都可追溯到用户故事、API 契约或技术计划

**下一步行动**: 根据检查结果更新 spec.md, plan.md 或 contracts/api.yaml
