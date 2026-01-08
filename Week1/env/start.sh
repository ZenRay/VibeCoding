#!/bin/bash
# Docker 环境启动脚本

set -e

echo "=========================================="
echo "Project Alpha - Docker 开发环境启动"
echo "=========================================="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! command -v docker compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 确定 docker-compose 命令
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# 进入 env 目录
cd "$(dirname "$0")"

echo ""
echo "📦 启动 Docker 服务..."
echo ""

# 启动服务
$DOCKER_COMPOSE up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "📊 服务状态："
$DOCKER_COMPOSE ps

echo ""
echo "=========================================="
echo "✅ Docker 环境启动完成！"
echo "=========================================="
echo ""
echo "访问地址："
echo "  📝 后端 API 文档 (Swagger UI): http://localhost:8000/docs"
echo "  📚 后端 API 文档 (ReDoc):     http://localhost:8000/redoc"
echo "  ❤️  健康检查:                  http://localhost:8000/health"
echo "  🗄️  数据库:                    localhost:5432"
echo ""
echo "常用命令："
echo "  查看日志:     $DOCKER_COMPOSE logs -f"
echo "  停止服务:     $DOCKER_COMPOSE down"
echo "  重启服务:     $DOCKER_COMPOSE restart"
echo "  查看状态:     $DOCKER_COMPOSE ps"
echo ""
echo "数据库迁移："
echo "  $DOCKER_COMPOSE exec backend alembic upgrade head"
echo ""
