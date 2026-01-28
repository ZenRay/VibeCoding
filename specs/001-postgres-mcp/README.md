# PostgreSQL 自然语言查询 MCP 服务器

**项目 ID**: 001-postgres-mcp
**状态**: 规格阶段（已完成）
**创建日期**: 2026-01-28

## 概述

基于 Python 的 MCP (Model Context Protocol) 服务器，允许用户使用自然语言查询 PostgreSQL 数据库。利用 OpenAI GPT-4o-mini 模型自动生成 SQL 查询，支持数据库 schema 缓存、安全验证和查询执行。

## 核心功能

- 🗣️ **自然语言转 SQL**: 将用户的自然语言描述转换为有效的 SQL 查询
- 📊 **Schema 智能缓存**: 启动时自动发现并缓存数据库结构（表、视图、列、索引、关系）
- 🔒 **安全验证**: 强制只读操作，阻止所有 INSERT/UPDATE/DELETE/DDL 语句
- ⚡ **即时执行**: 支持生成 SQL 或直接返回查询结果两种模式
- 🔄 **多数据库支持**: 同时连接和查询多个 PostgreSQL 数据库
- ✅ **结果验证**: 可选的 AI 驱动结果相关性检查

## 文档

- [功能规格说明](./spec.md) - 详细的业务需求和用户场景
- [质量检查清单](./checklists/requirements.md) - 规格验证结果

## 下一步

```bash
# 进入计划阶段
/speckit.plan

# 或先澄清需求（如需要）
/speckit.clarify
```

## 技术栈

- Python 3.12
- FastMCP 0.3+
- Asyncpg 0.29+
- SQLGlot 25.29+
- Pydantic 2.10+
- OpenAI GPT-4o-mini
- PostgreSQL 12.0+
- Docker 2.x (容器化部署)

## 成功标准

- ✅ 90%+ 准确率生成常见查询模式的 SQL
- ✅ 95% 的请求 5 秒内返回 SQL
- ✅ 100% 阻止数据修改操作
- ✅ 60 秒内完成多达 100 个表的 schema 缓存
- ✅ 99%+ 系统正常运行时间

## 优先级用户故事

### P1 - 核心功能（必须实现）
1. 自然语言查询转 SQL 生成
2. 数据库 Schema 发现和缓存
3. SQL 安全验证

### P2 - 增强功能
4. 执行查询并返回结果
5. 多数据库支持

### P3 - 质量提升
6. 查询结果验证

---

**项目位置**: `~/Documents/VibeCoding/Week5`
**规格位置**: `~/Documents/VibeCoding/specs/001-postgres-mcp`
