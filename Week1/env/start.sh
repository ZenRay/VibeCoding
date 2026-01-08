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

# 解析参数
MONITORING=false
TOOLS=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --monitoring|-m) MONITORING=true ;;
        --tools|-t) TOOLS=true ;;
        --all|-a) MONITORING=true; TOOLS=true ;;
        -h|--help)
            echo "用法: ./start.sh [选项]"
            echo ""
            echo "选项:"
            echo "  --monitoring, -m    启动监控服务 (Prometheus + Grafana)"
            echo "  --tools, -t         启动工具服务 (PgAdmin)"
            echo "  --all, -a           启动所有服务"
            echo "  -h, --help          显示帮助信息"
            exit 0
            ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
    shift
done

# 构建启动命令
PROFILES=""
if [ "$MONITORING" = true ]; then
    PROFILES="$PROFILES --profile monitoring"
fi
if [ "$TOOLS" = true ]; then
    PROFILES="$PROFILES --profile tools"
fi

echo ""
echo "📦 启动 Docker 服务..."
if [ -n "$PROFILES" ]; then
    echo "   启用配置:$PROFILES"
fi
echo ""

# 启动服务
$DOCKER_COMPOSE $PROFILES up -d

echo ""
echo "⏳ 等待服务启动..."
sleep 5

# 检查服务状态
echo ""
echo "📊 服务状态："
$DOCKER_COMPOSE $PROFILES ps

echo ""
echo "=========================================="
echo "✅ Docker 环境启动完成！"
echo "=========================================="
echo ""
echo "🌐 访问地址："
echo "  📝 后端 API 文档 (Swagger UI): http://localhost:8000/docs"
echo "  📚 后端 API 文档 (ReDoc):     http://localhost:8000/redoc"
echo "  ❤️  健康检查:                  http://localhost:8000/health"
echo "  📊 后端 Metrics:              http://localhost:8000/metrics"
echo "  🗄️  数据库:                    localhost:5432"

if [ "$MONITORING" = true ]; then
    echo ""
    echo "📈 监控服务："
    echo "  📊 Grafana:     http://localhost:3001 (admin/admin123)"
    echo "  🔍 Prometheus:  http://localhost:9090"
fi

if [ "$TOOLS" = true ]; then
    echo ""
    echo "🛠️  工具服务："
    echo "  🗃️  PgAdmin:     http://localhost:5050 (admin@example.com/admin123)"
fi

echo ""
echo "📋 常用命令："
echo "  查看日志:     $DOCKER_COMPOSE logs -f"
echo "  停止服务:     $DOCKER_COMPOSE down"
echo "  重启服务:     $DOCKER_COMPOSE restart"
echo "  查看状态:     $DOCKER_COMPOSE ps"
echo ""
echo "🚀 启动监控:    ./start.sh --monitoring"
echo "🛠️  启动工具:    ./start.sh --tools"
echo "📦 启动全部:    ./start.sh --all"
echo ""
echo "数据库迁移："
echo "  $DOCKER_COMPOSE exec backend alembic upgrade head"
echo ""
