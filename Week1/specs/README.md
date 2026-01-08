# Project Alpha 文档索引

本目录包含 Project Alpha 的所有技术文档。

**最后更新**：2026-01-09

## 📚 文档列表

### 基础文档（必读）

| 文档 | 说明 | 适用人员 |
|------|------|---------|
| [0001-spec.md](./0001-spec.md) | 需求规格说明 | 所有人 |
| [0002-implementation-plan.md](./0002-implementation-plan.md) | 实施计划 | 开发者、PM |
| [0006-quick-start.md](./0006-quick-start.md) | 快速开始 | 新成员 |

### 开发环境

| 文档 | 说明 | 适用人员 |
|------|------|---------|
| [0010-docker-development.md](./0010-docker-development.md) | Docker 开发环境完整指南 | 所有开发者 |
| [0006-quick-start.md](./0006-quick-start.md) | 快速开始指南 | 新成员 |

### 技术架构

| 文档 | 说明 | 适用人员 |
|------|------|---------|
| [0012-database-design.md](./0012-database-design.md) | 数据库设计和迁移 | 后端开发 |
| [0013-frontend-architecture.md](./0013-frontend-architecture.md) | 前端架构设计 | 前端开发 |
| [0003-features.md](./0003-features.md) | 功能说明文档 | 所有开发者 |

### 质量保证

| 文档 | 说明 | 适用人员 |
|------|------|---------|
| [0011-code-quality.md](./0011-code-quality.md) | 代码质量保证体系 | 所有开发者 |
| [0005-testing.md](./0005-testing.md) | 测试指南 | 开发者、QA |
| [0004-verification.md](./0004-verification.md) | 验证指南 | 开发者、QA |

### 工作流程

| 文档 | 说明 | 适用人员 |
|------|------|---------|
| [0007-git-workflow.md](./0007-git-workflow.md) | Git 工作流和 CI/CD | 所有开发者 |
| [0009-troubleshooting.md](./0009-troubleshooting.md) | 问题排查和解决方案 | 所有开发者 |
| [0014-lessons-learned.md](./0014-lessons-learned.md) | 经验教训和最佳实践 | 所有人 |

### 项目管理

| 文档 | 说明 | 适用人员 |
|------|------|---------|
| [0015-project-summary.md](./0015-project-summary.md) | 项目开发总结和成果 | 项目经理、技术负责人 |
| [0016-next-steps.md](./0016-next-steps.md) | 下一阶段计划 🆕 | 所有人 |
| [../PROJECT_STATUS.md](../PROJECT_STATUS.md) | 项目状态报告 | 所有人 |

### 元文档

| 文档 | 说明 | 适用人员 |
|------|------|---------|
| [0008-documentation-structure.md](./0008-documentation-structure.md) | 文档结构管理 | 文档维护者 |

---

## 🎯 快速导航

### 我是新成员，从哪里开始？

1. **快速开始（3分钟）** → [0006-quick-start.md](./0006-quick-start.md) ⭐
2. **了解项目** → [0001-spec.md](./0001-spec.md)
3. **Docker 环境** → [0010-docker-development.md](./0010-docker-development.md)
4. **常用命令** → [../env/快速参考.md](../env/快速参考.md)
5. **遇到问题** → [0009-troubleshooting.md](./0009-troubleshooting.md)

### 我要开发新功能

1. **查看功能列表** → [0003-features.md](./0003-features.md)
2. **查看实施计划** → [0002-implementation-plan.md](./0002-implementation-plan.md)
3. **了解架构** → [0012-database-design.md](./0012-database-design.md) / [0013-frontend-architecture.md](./0013-frontend-architecture.md)
4. **代码规范** → [0011-code-quality.md](./0011-code-quality.md)
5. **提交代码** → [0007-git-workflow.md](./0007-git-workflow.md)

### 我遇到问题了

1. **查看问题排查** → [0009-troubleshooting.md](./0009-troubleshooting.md)
2. **查看经验教训** → [0014-lessons-learned.md](./0014-lessons-learned.md)
3. **查看对应技术文档** → 根据问题类型选择

### 我要优化项目

1. **代码质量** → [0011-code-quality.md](./0011-code-quality.md)
2. **测试覆盖** → [0005-testing.md](./0005-testing.md)
3. **性能优化** → [0013-frontend-architecture.md](./0013-frontend-architecture.md)
4. **Docker 优化** → [0010-docker-development.md](./0010-docker-development.md)

---

## 📖 文档说明

### 文档分类

**Level 1 - 规划文档**（不可删除）
- 0001-spec.md
- 0002-implementation-plan.md

**Level 2 - 技术文档**
- 0010-docker-development.md
- 0011-code-quality.md
- 0012-database-design.md
- 0013-frontend-architecture.md

**Level 3 - 操作文档**
- 0003-features.md
- 0004-verification.md
- 0005-testing.md
- 0006-quick-start.md
- 0007-git-workflow.md

**Level 4 - 辅助文档**
- 0008-documentation-structure.md
- 0009-troubleshooting.md
- 0014-lessons-learned.md

### 文档维护

**更新频率**：
- **高频**：0009-troubleshooting.md（遇到问题就更新）
- **中频**：0003-features.md（新功能后更新）
- **低频**：0001-spec.md、0002-implementation-plan.md（里程碑更新）

**维护原则**：
1. 文档随项目进展持续更新
2. 重要变更需要更新相关文档
3. 定期审查文档准确性
4. 删除过时内容

---

## 🔗 外部资源

### 官方文档

- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **Docker**: https://docs.docker.com/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Tailwind CSS**: https://tailwindcss.com/docs

### 工具文档

- **Black**: https://black.readthedocs.io/
- **Prettier**: https://prettier.io/docs/
- **pytest**: https://docs.pytest.org/
- **Alembic**: https://alembic.sqlalchemy.org/

---

## 📊 文档统计

- **总文档数**：17 个（含 README）
- **总字数**：约 55,000 字
- **覆盖范围**：需求、设计、开发、测试、部署、运维、总结
- **最后更新**：2026-01-09

### 文档分类统计

| 类型 | 数量 | 说明 |
|------|------|------|
| 规划文档 | 2 | 需求规格、实施计划 |
| 技术文档 | 6 | Docker、代码质量、数据库、前端、经验、总结 |
| 操作文档 | 5 | 功能、验证、测试、快速开始、Git |
| 项目管理 | 2 | 下一阶段计划、项目状态 |
| 辅助文档 | 2 | 文档结构、问题排查 |

---

## 💡 使用建议

### 日常开发

**每天必看**：
- [env/快速参考.md](../env/快速参考.md) - 常用命令

**遇到问题**：
- [0009-troubleshooting.md](./0009-troubleshooting.md) - 问题排查

**提交代码**：
- [0007-git-workflow.md](./0007-git-workflow.md) - Git 工作流

### 技术学习

**后端技术栈**：
- [0012-database-design.md](./0012-database-design.md)
- [0011-code-quality.md](./0011-code-quality.md)

**前端技术栈**：
- [0013-frontend-architecture.md](./0013-frontend-architecture.md)
- [0011-code-quality.md](./0011-code-quality.md)

**DevOps**：
- [0010-docker-development.md](./0010-docker-development.md)
- [0007-git-workflow.md](./0007-git-workflow.md)

---

**文档持续更新中...** ✨
