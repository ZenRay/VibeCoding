#!/bin/bash
# Docker 容器启动脚本

set -e

echo "🚀 启动 Project Alpha Backend..."

# 等待数据库就绪
echo "⏳ 等待数据库连接..."
until PGPASSWORD=$POSTGRES_PASSWORD psql -h postgres -U ticketuser -d ticketdb -c '\q' 2>/dev/null; do
  >&2 echo "📦 PostgreSQL 未就绪，等待中..."
  sleep 1
done

echo "✅ 数据库连接成功！"

# 运行数据库迁移
echo "🔄 运行数据库迁移..."
.venv/bin/alembic upgrade head

echo "✅ 数据库迁移完成！"

# 启动应用
echo "🎯 启动 FastAPI 应用..."
exec "$@"
