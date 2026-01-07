#!/bin/bash
# 在运行中的 Docker 容器内执行检查
# 适用于已经启动 docker-compose 的情况

set -e

cd "$(dirname "$0")/.."

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🐳 在运行中的 Docker 容器内执查${NC}"
echo "================================"
echo ""

# 检查容器是否运行
if ! docker ps | grep -q project-alpha-backend; then
    echo -e "${RED}❌ backend 容器未运行${NC}"
    echo "请先启动 Docker 服务："
    echo "  cd env && ./start.sh"
    exit 1
fi

if ! docker ps | grep -q project-alpha-frontend; then
    echo -e "${RED}❌ frontend 容器未运行${NC}"
    echo "请先启动 Docker 服务："
    echo "  cd env && ./start.sh"
    exit 1
fi

# 后端检查
echo -e "${GREEN}=== 后端检查 ===${NC}"
echo ""

echo -e "${YELLOW}[1/4] Black 格式化检查...${NC}"
docker exec project-alpha-backend bash -c "
    source .venv/bin/activate && black --check --diff .
" && echo -e "${GREEN}✓ Black 检查通过${NC}" || {
    echo -e "${RED}✗ Black 检查失败，自动修复...${NC}"
    docker exec project-alpha-backend bash -c "source .venv/bin/activate && black ."
    echo -e "${YELLOW}已修复${NC}"
}

echo ""
echo -e "${YELLOW}[2/4] isort 检查...${NC}"
docker exec project-alpha-backend bash -c "
    source .venv/bin/activate && isort --check-only --diff .
" && echo -e "${GREEN}✓ isort 检查通过${NC}" || {
    echo -e "${RED}✗ isort 检查失败，自动修复...${NC}"
    docker exec project-alpha-backend bash -c "source .venv/bin/activate && isort ."
    echo -e "${YELLOW}已修复${NC}"
}

echo ""
echo -e "${YELLOW}[3/4] Ruff 检查...${NC}"
docker exec project-alpha-backend bash -c "
    source .venv/bin/activate && ruff check .
" && echo -e "${GREEN}✓ Ruff 检查通过${NC}" || {
    echo -e "${RED}✗ Ruff 检查失败，自动修复...${NC}"
    docker exec project-alpha-backend bash -c "source .venv/bin/activate && ruff check --fix ."
    echo -e "${YELLOW}已修复${NC}"
}

echo ""
echo -e "${YELLOW}[4/4] 运行测试...${NC}"
docker exec project-alpha-backend bash -c "
    source .venv/bin/activate && pytest --cov=app --cov-report=term -v
" && echo -e "${GREEN}✓ 测试通过${NC}" || {
    echo -e "${RED}✗ 测试失败${NC}"
    exit 1
}

# 前端检查
echo ""
echo -e "${GREEN}=== 前端检查 ===${NC}"
echo ""

echo -e "${YELLOW}[1/4] Prettier 格式化检查...${NC}"
docker exec project-alpha-frontend sh -c "
    npx prettier --check 'src/**/*.{ts,tsx,css}'
" && echo -e "${GREEN}✓ Prettier 检查通过${NC}" || {
    echo -e "${RED}✗ Prettier 检查失败，自动修复...${NC}"
    docker exec project-alpha-frontend sh -c "npx prettier --write 'src/**/*.{ts,tsx,css}'"
    echo -e "${YELLOW}已修复${NC}"
}

echo ""
echo -e "${YELLOW}[2/4] ESLint 检查...${NC}"
docker exec project-alpha-frontend sh -c "npm run lint" && \
    echo -e "${GREEN}✓ ESLint 检查通过${NC}" || {
    echo -e "${RED}✗ ESLint 检查失败${NC}"
    exit 1
}

echo ""
echo -e "${YELLOW}[3/4] TypeScript 类型检查...${NC}"
docker exec project-alpha-frontend sh -c "npm run type-check" && \
    echo -e "${GREEN}✓ TypeScript 检查通过${NC}" || {
    echo -e "${RED}✗ TypeScript 检查失败${NC}"
    exit 1
}

echo ""
echo -e "${YELLOW}[4/4] 构建检查...${NC}"
docker exec project-alpha-frontend sh -c "npm run build" && \
    echo -e "${GREEN}✓ 构建成功${NC}" || {
    echo -e "${RED}✗ 构建失败${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}🎉 所有检查通过！${NC}"
echo ""
echo "如有文件被修复，请运行："
echo "  git add -A"
echo "  git commit -m 'fix: Docker 环境自动修复代码'"
echo "  git push origin main"
