# Instructions

## project alpha 需求和设计文档

构建一个一个简单的，使用标签分类和管理 ticket 的工具。它基于 Postgres 数据库，使用 Fast API 作为后端，使用 Typescript/Vite/Tailwind/Shadcn 作为前端。无需用户系统，当前用户可以：

- 创建/编辑/删除/完成/取消完成 ticket
- 添加/删除 ticket 的标签
- 按照不同的标签查看 ticket 列表
- 按 title 搜索 ticket

按照这个想法，帮我生成详细的需求和设计文档，放在 ../specs/0001-spec.md 文件中，输出为中文。

## Document Mangement
1. 非开发的内容不需要存放太冗余的代码

### Git Management
1. 进行 Git 提交时，使用 pre-commit 检查
2. push 代码到 GitHub 时，使用 action 的能力

## Dev enviroment
1. 使用 docker 生成一个合适的开发环境，如有必要可以使用 dockercompsoe 生成一个服务。Docker 的管理需要放在 ../env 中
2. 声明清楚使用的技术栈及其需要的版本
3. docker compose 的服务启动环境是在 2.x，因此需要注意是否应当使用 `docker-compose`命令还是 `docker compose`


## Progress
- ✅ **需求和设计文档** (`specs/0001-spec.md`) - 已完成
  - 完整的功能需求
  - 数据库设计（PostgreSQL + 软删除）
  - RESTful API 设计
  - 前端 UI/UX 设计
  - 技术栈明确（Python 3.12 + UV，React + TypeScript）
  
- ✅ **实施计划** (`specs/0002-implementation-plan.md`) - v1.1 已完善
  - 7 个开发阶段，共 8-10 周
  - 125 个详细任务清单（新增 API 文档和测试相关任务）
  - 风险管理和缓解措施
  - 进度跟踪机制
  - 完整的 API 文档和测试工具指南

- ✅ **开发环境搭建** (阶段 0) - 已完成
  - Docker 环境配置完成
  - 启动和停止脚本已创建
- ✅ **数据库与后端基础** (阶段 1) - 已完成
  - 数据库模型实现完成
  - FastAPI 应用基础结构完成
  - Alembic 迁移配置完成
  - Docker 环境优化完成（大陆网络）
- ✅ **前端基础设施** (阶段 3) - 已完成
  - 项目结构搭建完成
  - TypeScript 类型定义完成
  - API 服务封装完成
  - 状态管理配置完成
  - 自定义 Hooks 实现完成
  - Docker 环境优化完成（大陆网络）
- ✅ **后端 API 实现** (阶段 2) - 已完成
  - Ticket Service 和 API Router 完成
  - Tag Service 和 API Router 完成
  - 搜索和过滤功能完成
  - 单元测试和集成测试完成
  - API 测试脚本已创建
- ✅ **前端核心功能** (阶段 4) - 已完成 85%
  - Sidebar 组件（状态过滤 + 标签过滤）
  - HomePage 列表布局（参考页面设计优化）
  - TicketListItem 组件（列表项 + 批量选择）
  - TicketDialog 和 TagDialog（创建/编辑）
  - 搜索和过滤功能（顶部搜索 + 侧边栏过滤）
  - 批量操作功能（批量选择和删除）
  - 排序功能（创建时间/更新时间/标题）
- ⚪ **前端扩展功能** (阶段 5) - 未开始
- ⚪ **测试与优化** (阶段 6) - 未开始
- ⚪ **部署与上线** (阶段 7) - 未开始

**项目总体进度：60.8% （已完成 76/125 个任务）**

## Implementation Plan
✅ 已完成 - 详细的实现计划已生成在 `../specs/0002-implementation-plan.md` 中

**实施计划概要**：
- **总预估时间**：8-10 周（全职开发）
- **MVP 版本**：4-5 周
- **总任务数**：125 个
- **关键里程碑**：6 个
- **开发阶段**：7 个
- **新增内容**：API 文档配置、测试工具使用、Swagger UI/ReDoc 集成

**下一步行动**：
1. 完成阶段 4 剩余任务：响应式设计、分页 UI、Toast 提示
2. 开始阶段 5：前端扩展功能（回收站、高级搜索）
3. 继续按照实施计划推进开发工作

## Impemente Stage
根据 `../spec/0002-impementation-plan.md`  完整实现这个项目中的 phase1 的代码。所有执行阶段的 `md` 文件都需要存放到 ../specs