# 监控系统使用指南

本文档说明如何使用 Project Alpha 的监控系统。

## 概述

监控系统包含以下组件：

| 组件 | 用途 | 端口 |
|------|------|------|
| Prometheus | 指标收集和存储 | 9090 |
| Grafana | 可视化仪表盘 | 3001 |
| postgres-exporter | PostgreSQL 指标导出 | 9187 |
| FastAPI /metrics | 后端应用指标 | 8000 |

## 快速开始

### 启动监控服务

```bash
cd Week1/env

# 方式1：仅启动监控
./start.sh --monitoring

# 方式2：启动所有服务（包含监控和工具）
./start.sh --all

# 方式3：手动指定 profile
docker compose --profile monitoring up -d
```

### 访问地址

- **Grafana**: http://localhost:3001
  - 用户名: `admin`
  - 密码: `admin123`

- **Prometheus**: http://localhost:9090

- **后端 Metrics**: http://localhost:8000/metrics

## Grafana 仪表盘

系统预配置了两个仪表盘：

### 1. FastAPI 监控仪表盘

展示后端 API 的运行状态：

- **请求速率** - 每秒请求数
- **P95 响应延迟** - 95% 请求的响应时间
- **HTTP 请求趋势** - 按方法（GET/POST/PUT/DELETE）分类
- **响应延迟分布** - P50/P90/P99 延迟曲线
- **HTTP 状态码分布** - 2xx/4xx/5xx 比例
- **请求分布（按端点）** - 各 API 端点的调用量

### 2. PostgreSQL 监控仪表盘

展示数据库的运行状态：

- **数据库状态** - Up/Down 状态指示
- **活跃连接数** - 当前数据库连接数
- **数据库大小** - ticketdb 占用空间
- **运行时间** - PostgreSQL 运行时长
- **事务速率** - 提交/回滚事务速率
- **行操作速率** - 返回/获取行数速率
- **连接数趋势** - 活跃/空闲连接变化

## Prometheus 查询示例

在 Prometheus 界面（http://localhost:9090）可以执行 PromQL 查询：

```promql
# 请求速率（每分钟）
rate(http_requests_total[1m])

# P95 延迟
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# 错误率
sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))

# 数据库连接数
pg_stat_activity_count

# 数据库大小
pg_database_size_bytes{datname="ticketdb"}
```

## 指标说明

### FastAPI 指标（prometheus-fastapi-instrumentator）

| 指标名 | 类型 | 说明 |
|--------|------|------|
| `http_requests_total` | Counter | HTTP 请求总数 |
| `http_request_duration_seconds` | Histogram | 请求延迟分布 |
| `http_requests_in_progress` | Gauge | 正在处理的请求数 |

### PostgreSQL 指标（postgres-exporter）

| 指标名 | 类型 | 说明 |
|--------|------|------|
| `pg_up` | Gauge | 数据库是否可用 |
| `pg_stat_activity_count` | Gauge | 连接数 |
| `pg_database_size_bytes` | Gauge | 数据库大小 |
| `pg_stat_database_xact_commit` | Counter | 提交事务数 |
| `pg_stat_database_xact_rollback` | Counter | 回滚事务数 |

## 停止监控服务

```bash
# 停止所有服务
docker compose --profile monitoring down

# 仅停止监控服务（保留核心服务）
docker stop week1-prometheus week1-grafana week1-postgres-exporter
```

## 数据持久化

监控数据存储在 Docker volumes 中：

- `week1_prometheus_data` - Prometheus 时序数据
- `week1_grafana_data` - Grafana 配置和仪表盘

清理数据：

```bash
# 警告：这将删除所有监控历史数据
docker volume rm week1_prometheus_data week1_grafana_data
```

## 告警配置（高级）

如需配置告警，可以：

1. **Prometheus Alertmanager**（推荐生产环境）
   - 在 `prometheus/` 目录添加告警规则
   - 配置 Alertmanager 服务

2. **Grafana 告警**（简单场景）
   - 在 Grafana 仪表盘中配置 Alert
   - 支持邮件、Slack、Webhook 等通知方式

## 故障排查

### 监控服务无法启动

```bash
# 检查端口占用
lsof -i :9090  # Prometheus
lsof -i :3001  # Grafana
lsof -i :9187  # postgres-exporter

# 查看容器日志
docker logs week1-prometheus
docker logs week1-grafana
docker logs week1-postgres-exporter
```

### Grafana 无数据显示

1. 确认 Prometheus 正在运行：访问 http://localhost:9090/targets
2. 确认后端 `/metrics` 端点可访问：访问 http://localhost:8000/metrics
3. 检查 Grafana 数据源配置：Settings → Data Sources → Prometheus

### Prometheus 抓取失败

```bash
# 检查目标状态
curl http://localhost:9090/api/v1/targets

# 检查后端 metrics 端点
curl http://localhost:8000/metrics
```

## 相关文档

- [Docker 环境配置](./README.md)
- [快速参考](./快速参考.md)
- [Prometheus 官方文档](https://prometheus.io/docs/)
- [Grafana 官方文档](https://grafana.com/docs/)
