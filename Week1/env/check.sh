#!/bin/bash
# 在 Docker 中运行所有检查（使用临时容器）
# 优势：不依赖运行中的容器，与 CI 环境完全一致

set -e

cd "$(dirname "$0")"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🐳 Docker 环境检查（临时容器）${NC}"
echo "================================"
echo ""

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker 未运行，请先启动 Docker${NC}"
    exit 1
fi

# 后端检查
echo -e "${GREEN}=== 后端检查（Python 3.12） ===${NC}"
echo ""

echo -e "${YELLOW}[1/4] Black 格式化检查...${NC}"
docker run --rm -v "$(pwd)/../backend:/app" -w /app python:3.12-slim bash -c "
    apt-get update -qq && apt-get install -y -qq git > /dev/null 2>&1 &&
    pip install -q black &&
    black --check --diff .
" && echo -e "${GREEN}✓ Black 检查通过${NC}" || {
    echo -e "${RED}✗ Black 检查失败，自动修复...${NC}"
    docker run --rm -v "$(pwd)/../backend:/app" -w /app python:3.12-slim bash -c "
        apt-get update -qq && apt-get install -y -qq git > /dev/null 2>&1 &&
        pip install -q black &&
        black .
    "
    echo -e "${YELLOW}已修复，需要提交${NC}"
}

echo ""
echo -e "${YELLOW}[2/4] isort 导入排序检查...${NC}"
docker run --rm -v "$(pwd)/../backend:/app" -w /app python:3.12-slim bash -c "
    apt-get update -qq && apt-get install -y -qq git > /dev/null 2>&1 &&
    pip install -q isort &&
    isort --check-only --diff .
" && echo -e "${GREEN}✓ isort 检查通过${NC}" || {
    echo -e "${RED}✗ isort 检查失败，自动修复...${NC}"
    docker run --rm -v "$(pwd)/../backend:/app" -w /app python:3.12-slim bash -c "
        apt-get update -qq && apt-get install -y -qq git > /dev/null 2>&1 &&
        pip install -q isort &&
        isort .
    "
    echo -e "${YELLOW}已修复，需要提交${NC}"
}

echo ""
echo -e "${YELLOW}[3/4] Ruff 代码检查...${NC}"
docker run --rm -v "$(pwd)/../backend:/app" -w /app python:3.12-slim bash -c "
    apt-get update -qq && apt-get install -y -qq git > /dev/null 2>&1 &&
    pip install -q ruff &&
    ruff check .
" && echo -e "${GREEN}✓ Ruff 检查通过${NC}" || {
    echo -e "${RED}✗ Ruff 检查失败，自动修复...${NC}"
    docker run --rm -v "$(pwd)/../backend:/app" -w /app python:3.12-slim bash -c "
        apt-get update -qq && apt-get install -y -qq git > /dev/null 2>&1 &&
        pip install -q ruff &&
        ruff check --fix .
    "
    echo -e "${YELLOW}已修复，需要提交${NC}"
}

echo ""
echo -e "${YELLOW}[4/4] 运行后端测试...${NC}"
docker run --rm -v "$(pwd)/../backend:/app" -w /app python:3.12-slim bash -c "
    apt-get update -qq && apt-get install -y -qq git gcc libpq-dev > /dev/null 2>&1 &&
    pip install -q -e '.[dev]' &&
    pytest --cov=app --cov-report=term
" && echo -e "${GREEN}✓ 测试通过${NC}" || {
    echo -e "${RED}✗ 测试失败${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}=== 后端检查完成 ===${NC}\n"

# 前端检查
echo -e "${GREEN}=== 前端检查（Node 20） ===${NC}"
echo ""

echo -e "${YELLOW}[1/4] Prettier 格式化检查...${NC}"
docker run --rm -v "$(pwd)/../frontend:/app" -w /app node:20-alpine sh -c "
    npm install > /dev/null 2>&1 &&
    npx prettier --check 'src/**/*.{ts,tsx,css}'
" && echo -e "${GREEN}✓ Prettier 检查通过${NC}" || {
    echo -e "${RED}✗ Prettier 检查失败，自动修复...${NC}"
    docker run --rm -v "$(pwd)/../frontend:/app" -w /app node:20-alpine sh -c "
        npm install > /dev/null 2>&1 &&
        npx prettier --write 'src/**/*.{ts,tsx,css}'
    "
    echo -e "${YELLOW}已修复，需要提交${NC}"
}

echo ""
echo -e "${YELLOW}[2/4] ESLint 检查...${NC}"
docker run --rm -v "$(pwd)/../frontend:/app" -w /app node:20-alpine sh -c "
    npm install > /dev/null 2>&1 &&
    npm run lint
" && echo -e "${GREEN}✓ ESLint 检查通过${NC}" || {
    echo -e "${RED}✗ ESLint 检查失败${NC}"
    exit 1
}

echo ""
echo -e "${YELLOW}[3/4] TypeScript 类型检查...${NC}"
docker run --rm -v "$(pwd)/../frontend:/app" -w /app node:20-alpine sh -c "
    npm install > /dev/null 2>&1 &&
    npm run type-check
" && echo -e "${GREEN}✓ TypeScript 检查通过${NC}" || {
    echo -e "${RED}✗ TypeScript 检查失败${NC}"
    exit 1
}

echo ""
echo -e "${YELLOW}[4/4] 构建检查...${NC}"
docker run --rm -v "$(pwd)/../frontend:/app" -w /app node:20-alpine sh -c "
    npm install > /dev/null 2>&1 &&
    npm run build
" && echo -e "${GREEN}✓ 构建成功${NC}" || {
    echo -e "${RED}✗ 构建失败${NC}"
    exit 1
}

echo ""
echo -e "${GREEN}=== 前端检查完成 ===${NC}\n"

echo -e "${GREEN}🎉 所有检查通过！${NC}"
echo ""
echo "如有文件被修复，请运行："
echo "  git add -A"
echo "  git commit -m 'fix: 修复代码格式和质量问题'"
echo "  git push origin main"
