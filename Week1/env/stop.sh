#!/bin/bash
# Docker 环境停止脚本

set -e

# 确定 docker-compose 命令
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

# 进入 env 目录
cd "$(dirname "$0")"

echo "🛑 停止 Docker 服务..."
$DOCKER_COMPOSE down

echo "✅ Docker 服务已停止"
