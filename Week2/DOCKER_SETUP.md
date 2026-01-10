# Docker 服务设置指南

## 概述

本项目使用 Docker Compose 管理测试数据库服务（PostgreSQL 和 MySQL），用于开发和测试。

## 启动测试数据库

### 启动所有数据库服务

```bash
cd Week2/env
docker compose up -d postgres mysql
```

### 检查服务状态

```bash
docker compose ps
```

### 查看服务日志

```bash
# PostgreSQL 日志
docker logs db-query-tool-postgres

# MySQL 日志
docker logs db-query-tool-mysql
```

## 测试数据库连接信息

### PostgreSQL

- **URL**: `postgresql://postgres:postgres@localhost:5432/testdb`
- **用户**: `postgres`
- **密码**: `postgres`
- **数据库**: `testdb`
- **端口**: `5432`

### MySQL

- **URL**: `mysql://testuser:testpass@localhost:3306/testdb`
- **用户**: `testuser`
- **密码**: `testpass`
- **数据库**: `testdb`
- **端口**: `3306`

## 预置测试数据

两个数据库都包含以下测试表：

- **users**: 用户表（id, name, email, age, created_at）
- **orders**: 订单表（id, user_id, product_name, quantity, price, order_date）
- **products**: 产品表（id, name, description, price, stock, created_at）
- **user_order_summary**: 视图（用户订单汇总）

## 停止服务

```bash
cd Week2/env
docker compose stop postgres mysql
```

## 删除数据卷（重置数据）

```bash
docker compose down -v
```

## 注意事项

1. **首次启动**: 首次启动时会自动执行初始化脚本，创建测试表和测试数据
2. **数据持久化**: 数据存储在 Docker volumes 中，重启容器不会丢失数据
3. **端口冲突**: 确保本地 5432 和 3306 端口未被占用
4. **网络**: 服务运行在 `db-network` Docker 网络中

## 验证连接

### 使用 curl 测试

```bash
# 添加 PostgreSQL 连接
curl -X PUT "http://localhost:8000/api/v1/dbs/test-postgres" \
  -H "Content-Type: application/json" \
  -d '{"url": "postgresql://postgres:postgres@localhost:5432/testdb"}'

# 添加 MySQL 连接
curl -X PUT "http://localhost:8000/api/v1/dbs/test-mysql" \
  -H "Content-Type: application/json" \
  -d '{"url": "mysql://testuser:testpass@localhost:3306/testdb"}'
```

### 使用 Docker 命令测试

```bash
# 测试 PostgreSQL
docker exec db-query-tool-postgres psql -U postgres -d testdb -c "SELECT 1"

# 测试 MySQL
docker exec db-query-tool-mysql mysql -utestuser -ptestpass -e "SELECT 1"
```
