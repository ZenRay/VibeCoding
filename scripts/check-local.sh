#!/bin/bash
# 本地 CI 检查脚本
# 用法: ./scripts/check-local.sh [backend|frontend|all]

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查函数
check_backend() {
    echo -e "${GREEN}=== 后端检查 ===${NC}"
    cd backend || exit 1

    # 检查虚拟环境
    if [ ! -d ".venv" ]; then
        echo -e "${YELLOW}创建虚拟环境...${NC}"
        python3 -m venv .venv || uv venv
    fi

    # 激活虚拟环境
    source .venv/bin/activate

    # 安装依赖
    echo -e "${YELLOW}安装依赖...${NC}"
    if command -v uv &> /dev/null; then
        uv pip install -e ".[dev]" || pip install -e ".[dev]"
    else
        pip install -e ".[dev]"
    fi

    # Black 检查
    echo -e "${GREEN}[1/5] 运行 Black 格式化检查...${NC}"
    if black --check --diff .; then
        echo -e "${GREEN}✓ Black 检查通过${NC}"
    else
        echo -e "${RED}✗ Black 检查失败，运行 black --write . 自动修复${NC}"
        black --write .
        exit 1
    fi

    # isort 检查
    echo -e "${GREEN}[2/5] 运行 isort 导入排序检查...${NC}"
    if isort --check-only --diff .; then
        echo -e "${GREEN}✓ isort 检查通过${NC}"
    else
        echo -e "${RED}✗ isort 检查失败，运行 isort . 自动修复${NC}"
        isort .
        exit 1
    fi

    # Ruff 检查
    echo -e "${GREEN}[3/5] 运行 Ruff 代码检查...${NC}"
    if ruff check .; then
        echo -e "${GREEN}✓ Ruff 检查通过${NC}"
    else
        echo -e "${RED}✗ Ruff 检查失败，运行 ruff check --fix . 自动修复${NC}"
        ruff check --fix .
        exit 1
    fi

    # mypy 检查（可选，不阻塞）
    echo -e "${GREEN}[4/5] 运行 mypy 类型检查...${NC}"
    if mypy app --ignore-missing-imports 2>/dev/null || true; then
        echo -e "${GREEN}✓ mypy 检查完成${NC}"
    else
        echo -e "${YELLOW}⚠ mypy 检查有警告（非阻塞）${NC}"
    fi

    # 运行测试
    echo -e "${GREEN}[5/5] 运行测试...${NC}"
    if pytest --cov=app --cov-report=term -v; then
        echo -e "${GREEN}✓ 测试通过${NC}"
    else
        echo -e "${RED}✗ 测试失败${NC}"
        exit 1
    fi

    cd ..
    echo -e "${GREEN}=== 后端检查完成 ===${NC}\n"
}

check_frontend() {
    echo -e "${GREEN}=== 前端检查 ===${NC}"
    cd frontend || exit 1

    # 检查 node_modules
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}安装依赖...${NC}"
        npm install
    fi

    # ESLint 检查
    echo -e "${GREEN}[1/4] 运行 ESLint...${NC}"
    if npm run lint; then
        echo -e "${GREEN}✓ ESLint 检查通过${NC}"
    else
        echo -e "${RED}✗ ESLint 检查失败${NC}"
        exit 1
    fi

    # Prettier 检查
    echo -e "${GREEN}[2/4] 运行 Prettier 格式化检查...${NC}"
    if npx prettier --check "src/**/*.{ts,tsx,css}"; then
        echo -e "${GREEN}✓ Prettier 检查通过${NC}"
    else
        echo -e "${RED}✗ Prettier 检查失败，运行 npx prettier --write 自动修复${NC}"
        npx prettier --write "src/**/*.{ts,tsx,css}"
        exit 1
    fi

    # TypeScript 类型检查
    echo -e "${GREEN}[3/4] 运行 TypeScript 类型检查...${NC}"
    if npm run type-check; then
        echo -e "${GREEN}✓ TypeScript 检查通过${NC}"
    else
        echo -e "${RED}✗ TypeScript 检查失败${NC}"
        exit 1
    fi

    # 构建检查
    echo -e "${GREEN}[4/4] 运行构建检查...${NC}"
    if npm run build; then
        echo -e "${GREEN}✓ 构建成功${NC}"
    else
        echo -e "${RED}✗ 构建失败${NC}"
        exit 1
    fi

    cd ..
    echo -e "${GREEN}=== 前端检查完成 ===${NC}\n"
}

# 主逻辑
case "${1:-all}" in
    backend)
        check_backend
        ;;
    frontend)
        check_frontend
        ;;
    all)
        check_backend
        check_frontend
        echo -e "${GREEN}🎉 所有检查通过！可以安全提交代码了。${NC}"
        ;;
    *)
        echo "用法: $0 [backend|frontend|all]"
        exit 1
        ;;
esac
