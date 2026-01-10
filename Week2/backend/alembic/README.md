# Alembic 迁移脚本使用指南

## 概述

本项目使用 Alembic 管理本地 SQLite 数据库的模式版本变更。

## 目录结构

```
alembic/
├── env.py              # Alembic 环境配置
├── script.py.mako      # 迁移脚本模板
└── versions/           # 迁移脚本目录
    └── 20260110_000001_initial_migration.py
```

## 常用命令

### 创建新迁移

```bash
cd Week2/backend
alembic revision --autogenerate -m "描述信息"
```

### 应用迁移

```bash
alembic upgrade head
```

### 回滚迁移

```bash
alembic downgrade -1
```

### 查看当前版本

```bash
alembic current
```

### 查看迁移历史

```bash
alembic history
```

## 迁移规则

1. **向前兼容**: 每次迁移必须包含 `upgrade()` 和 `downgrade()` 函数
2. **数据保留**: 迁移不应删除用户数据，仅修改模式
3. **版本追踪**: 在 `alembic_version` 表中记录当前版本
4. **自动应用**: 应用启动时自动检查并应用待执行的迁移

## 注意事项

- 迁移脚本应放在 `alembic/versions/` 目录
- 迁移脚本命名格式: `YYYYMMDD_HHMMSS_description.py`
- 不要手动修改已应用的迁移脚本
- 测试环境应先测试迁移脚本
