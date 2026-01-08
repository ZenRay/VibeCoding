# Instructions

## Project Alpha 需求和设计文档

构建一个简单的，使用标签分类和管理 ticket 的工具。它基于 Postgres 数据库，使用 FastAPI 作为后端，使用 TypeScript/Vite/Tailwind/Shadcn 作为前端。无需用户系统，当前用户可以：

- 创建/编辑/删除/完成/取消完成 ticket
- 添加/删除 ticket 的标签
- 按照不同的标签查看 ticket 列表
- 按 title 搜索 ticket

---

## Document Management

1. 非开发的内容不需要存放太冗余的代码
2. 关于项目说明和项目进度的 md 文件在 `../specs` 中完成
3. 测试文件统一存放到 `../tests` 中，该目录中的内容不需要 git 管理

## Progress Management
1. 对于不同阶段的管理统一使用 `../specs/spec-progess.md` 进行管理
2. 重要的更新，需要及时更新 `../specs/spec-progess.md` 文档

1. 项目状态使用 `../PROJECT_STATUS.md` 进行管理
2. 下一阶段计划使用 `../specs/0016-next-steps.md` 进行管理
3. 重要的更新，需要及时更新相关文档

## Git Management

1. 进行 Git 提交时，使用 pre-commit 检查
2. push 代码到 GitHub 时，使用 action 的能力

## Dev enviroment
1. 使用 Docker 生成开发环境，配置文件在 `../env` 目录
2. 声明清楚使用的技术栈及其需要的版本
3.  使用 `docker compose` 命令（Docker Compose V2）
4. 需要注意检查一下 `docker` 中 `compose` 和 `dockerfile` 文件是否存在问题


---

## Progress

**最后更新**：2026-01-09  
**当前版本**：v0.1.0（功能完整版）  
**总体进度**：90% 🎯

### 开发阶段完成情况

| 阶段 | 名称 | 状态 | 完成度 |
|------|------|------|--------|
| 阶段 0 | 环境准备 | ✅ 完成 | 100% |
| 阶段 1 | 数据库与后端基础 | ✅ 完成 | 100% |
| 阶段 2 | 后端 API 实现 | ✅ 完成 | 100% |
| 阶段 3 | 前端基础设施 | ✅ 完成 | 100% |
| 阶段 4 | 前端核心功能 | ✅ 完成 | 100% |
| 阶段 4.5 | 环境和文档完善 | ✅ 完成 | 100% |
| 阶段 5 | 前端扩展功能 | ✅ 完成 | 100% |
| 阶段 6 | 测试与优化 | 🔵 部分完成 | 50% |
| 阶段 7 | 部署与上线 | ⚪ 未开始 | 0% |

### 已完成功能 ✅

**后端** (100%):
- Ticket CRUD + 软删除/恢复
- Tag CRUD + 自动大写
- 高级搜索、过滤、排序、分页
- 单元测试 + 集成测试（35 个，覆盖率 82%）

**前端** (100%):
- Ticket 列表（列表布局 + 侧边栏）
- 创建/编辑/删除/恢复 + 状态切换
- 搜索（实时 + 防抖）+ 过滤 + 排序
- 批量操作 + 软删除视觉效果
- Toast 提示 + 骨架屏 + 分页 + 键盘快捷键
- 回收站页面 + 错误边界

**基础设施** (100%):
- Docker 开发环境 + CI/CD
- 17 个技术文档

### 待完成

**阶段 6 剩余**（P0 - 必须）：
- E2E 测试（Playwright）
- 性能优化

**阶段 7**（P1 - 推荐）：
- 精简部署上线

详细计划请查看 `../specs/0016-next-steps.md`

---

## 相关文档

- [PROJECT_STATUS.md](../PROJECT_STATUS.md) - 项目状态报告
- [specs/0016-next-steps.md](../specs/0016-next-steps.md) - 下一阶段计划
- [specs/0002-implementation-plan.md](../specs/0002-implementation-plan.md) - 完整实施计划
- [specs/0006-quick-start.md](../specs/0006-quick-start.md) - 快速开始
- [文档导航.md](../文档导航.md) - 文档导航
