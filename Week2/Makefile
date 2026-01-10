.PHONY: help install install-backend install-frontend init-db start start-backend start-frontend start-db stop stop-backend stop-frontend stop-db restart test test-backend test-frontend lint lint-backend lint-frontend format format-backend format-frontend clean clean-backend clean-frontend clean-all migrate migrate-create migrate-upgrade migrate-downgrade migrate-history setup dev check

# 颜色定义
COLOR_RESET := \033[0m
COLOR_BOLD := \033[1m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_BLUE := \033[34m

# 目录定义
BACKEND_DIR := backend
FRONTEND_DIR := frontend
ENV_DIR := env
DATA_DIR := data

# Python 虚拟环境
VENV := $(BACKEND_DIR)/.venv
VENV_BIN := $(VENV)/bin
PYTHON := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip
UV := uv

# 默认目标
.DEFAULT_GOAL := help

help: ## 显示帮助信息
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)数据库查询工具 - Makefile 命令$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BOLD)安装和设置:$(COLOR_RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(COLOR_GREEN)%-20s$(COLOR_RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(install|init|setup|migrate)"
	@echo ""
	@echo "$(COLOR_BOLD)启动和停止:$(COLOR_RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(COLOR_GREEN)%-20s$(COLOR_RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(start|stop|restart|dev)"
	@echo ""
	@echo "$(COLOR_BOLD)测试和代码质量:$(COLOR_RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(COLOR_GREEN)%-20s$(COLOR_RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "(test|lint|format|check)"
	@echo ""
	@echo "$(COLOR_BOLD)清理:$(COLOR_RESET)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(COLOR_GREEN)%-20s$(COLOR_RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST) | grep -E "clean"
	@echo ""

# ============================================================================
# 安装和设置
# ============================================================================

install: install-backend install-frontend ## 安装所有依赖（后端和前端）

install-backend: ## 安装后端依赖
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)安装后端依赖...$(COLOR_RESET)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "创建 Python 虚拟环境..."; \
		cd $(BACKEND_DIR) && $(UV) venv .venv; \
	fi
	@cd $(BACKEND_DIR) && $(UV) pip install --python .venv/bin/python -e ".[dev]"
	@echo "$(COLOR_GREEN)✓ 后端依赖安装完成$(COLOR_RESET)"

install-frontend: ## 安装前端依赖
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)安装前端依赖...$(COLOR_RESET)"
	@cd $(FRONTEND_DIR) && npm install
	@echo "$(COLOR_GREEN)✓ 前端依赖安装完成$(COLOR_RESET)"

init-db: ## 初始化数据库（运行迁移）
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)初始化数据库...$(COLOR_RESET)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(COLOR_YELLOW)警告: 虚拟环境不存在，请先运行 make install-backend$(COLOR_RESET)"; \
		exit 1; \
	fi
	@mkdir -p $(DATA_DIR)
	@cd $(BACKEND_DIR) && $(VENV_BIN)/alembic upgrade head
	@echo "$(COLOR_GREEN)✓ 数据库初始化完成$(COLOR_RESET)"

setup: install init-db ## 完整设置（安装依赖 + 初始化数据库）
	@echo "$(COLOR_GREEN)✓ 项目设置完成！$(COLOR_RESET)"
	@echo ""
	@echo "下一步："
	@echo "  1. 启动测试数据库: $(COLOR_BOLD)make start-db$(COLOR_RESET)"
	@echo "  2. 启动开发服务器: $(COLOR_BOLD)make dev$(COLOR_RESET)"

# ============================================================================
# 启动和停止服务
# ============================================================================

start: start-db start-backend start-frontend ## 启动所有服务（数据库 + 后端 + 前端）

start-backend: ## 启动后端服务（端口 8000）
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)启动后端服务...$(COLOR_RESET)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(COLOR_YELLOW)错误: 虚拟环境不存在，请先运行 make install-backend$(COLOR_RESET)"; \
		exit 1; \
	fi
	@cd $(BACKEND_DIR) && $(VENV_BIN)/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

start-frontend: ## 启动前端开发服务器（端口 3000）
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)启动前端服务...$(COLOR_RESET)"
	@cd $(FRONTEND_DIR) && npm run dev

start-db: ## 启动测试数据库（PostgreSQL + MySQL）
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)启动测试数据库...$(COLOR_RESET)"
	@cd $(ENV_DIR) && docker compose up -d postgres mysql
	@echo "$(COLOR_GREEN)✓ 数据库服务已启动$(COLOR_RESET)"
	@echo "等待数据库就绪..."
	@sleep 3
	@cd $(ENV_DIR) && docker compose ps

stop: stop-backend stop-frontend stop-db ## 停止所有服务

stop-backend: ## 停止后端服务
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)停止后端服务...$(COLOR_RESET)"
	@pkill -f "uvicorn app.main:app" || echo "后端服务未运行"
	@echo "$(COLOR_GREEN)✓ 后端服务已停止$(COLOR_RESET)"

stop-frontend: ## 停止前端服务
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)停止前端服务...$(COLOR_RESET)"
	@pkill -f "vite" || echo "前端服务未运行"
	@echo "$(COLOR_GREEN)✓ 前端服务已停止$(COLOR_RESET)"

stop-db: ## 停止测试数据库
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)停止测试数据库...$(COLOR_RESET)"
	@cd $(ENV_DIR) && docker compose stop postgres mysql
	@echo "$(COLOR_GREEN)✓ 数据库服务已停止$(COLOR_RESET)"

restart: stop start ## 重启所有服务

dev: start-db ## 启动开发环境（数据库 + 后端 + 前端，后台运行）
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)启动开发环境...$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)提示: 后端和前端将在后台运行$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)使用 'make stop' 停止所有服务$(COLOR_RESET)"
	@cd $(BACKEND_DIR) && $(VENV_BIN)/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/backend.log 2>&1 &
	@cd $(FRONTEND_DIR) && npm run dev > /tmp/frontend.log 2>&1 &
	@sleep 2
	@echo "$(COLOR_GREEN)✓ 开发环境已启动$(COLOR_RESET)"
	@echo ""
	@echo "服务地址："
	@echo "  前端: $(COLOR_BOLD)http://localhost:3000$(COLOR_RESET)"
	@echo "  后端 API: $(COLOR_BOLD)http://localhost:8000$(COLOR_RESET)"
	@echo "  API 文档: $(COLOR_BOLD)http://localhost:8000/docs$(COLOR_RESET)"
	@echo ""
	@echo "查看日志："
	@echo "  后端: $(COLOR_BOLD)tail -f /tmp/backend.log$(COLOR_RESET)"
	@echo "  前端: $(COLOR_BOLD)tail -f /tmp/frontend.log$(COLOR_RESET)"

# ============================================================================
# 数据库迁移
# ============================================================================

migrate-create: ## 创建新的数据库迁移（用法: make migrate-create MESSAGE="描述"）
	@if [ -z "$(MESSAGE)" ]; then \
		echo "$(COLOR_YELLOW)错误: 请提供迁移描述$(COLOR_RESET)"; \
		echo "用法: make migrate-create MESSAGE=\"你的描述\""; \
		exit 1; \
	fi
	@cd $(BACKEND_DIR) && $(VENV_BIN)/alembic revision --autogenerate -m "$(MESSAGE)"
	@echo "$(COLOR_GREEN)✓ 迁移文件已创建$(COLOR_RESET)"

migrate-upgrade: ## 升级数据库到最新版本
	@cd $(BACKEND_DIR) && $(VENV_BIN)/alembic upgrade head
	@echo "$(COLOR_GREEN)✓ 数据库已升级$(COLOR_RESET)"

migrate-downgrade: ## 降级数据库一个版本（用法: make migrate-downgrade REVISION="-1"）
	@if [ -z "$(REVISION)" ]; then \
		echo "$(COLOR_YELLOW)错误: 请指定版本$(COLOR_RESET)"; \
		echo "用法: make migrate-downgrade REVISION=\"-1\" 或 REVISION=\"base\""; \
		exit 1; \
	fi
	@cd $(BACKEND_DIR) && $(VENV_BIN)/alembic downgrade $(REVISION)
	@echo "$(COLOR_GREEN)✓ 数据库已降级$(COLOR_RESET)"

migrate-history: ## 显示迁移历史
	@cd $(BACKEND_DIR) && $(VENV_BIN)/alembic history

migrate: migrate-upgrade ## 运行数据库迁移（升级到最新版本）

# ============================================================================
# 测试
# ============================================================================

test: test-backend test-frontend ## 运行所有测试

test-backend: ## 运行后端测试
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)运行后端测试...$(COLOR_RESET)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(COLOR_YELLOW)错误: 虚拟环境不存在，请先运行 make install-backend$(COLOR_RESET)"; \
		exit 1; \
	fi
	cd $(BACKEND_DIR) && $(PYTHON) -m pytest -v

test-frontend: ## 运行前端测试
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)运行前端测试...$(COLOR_RESET)"
	@cd $(FRONTEND_DIR) && npm test || echo "前端测试未配置"

# ============================================================================
# 代码质量
# ============================================================================

lint: lint-backend lint-frontend ## 运行所有代码检查

lint-backend: ## 检查后端代码
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)检查后端代码...$(COLOR_RESET)"
	@test -d "$(VENV)" || (echo "$(COLOR_YELLOW)错误: 虚拟环境不存在，请先运行 make install-backend$(COLOR_RESET)" && exit 1)
	@test -f "$(PYTHON)" || (echo "$(COLOR_YELLOW)错误: Python 不存在于 $(PYTHON)，请运行 make install-backend$(COLOR_RESET)" && exit 1)
	$(PYTHON) -m ruff check $(BACKEND_DIR) || true
	$(PYTHON) -m mypy $(BACKEND_DIR)/app || true
	@echo "$(COLOR_GREEN)✓ 后端代码检查完成$(COLOR_RESET)"

lint-frontend: ## 检查前端代码
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)检查前端代码...$(COLOR_RESET)"
	@cd $(FRONTEND_DIR) && npm run lint || true
	@cd $(FRONTEND_DIR) && npm run type-check || true
	@echo "$(COLOR_GREEN)✓ 前端代码检查完成$(COLOR_RESET)"

format: format-backend format-frontend ## 格式化所有代码

format-backend: ## 格式化后端代码
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)格式化后端代码...$(COLOR_RESET)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(COLOR_YELLOW)错误: 虚拟环境不存在，请先运行 make install-backend$(COLOR_RESET)"; \
		exit 1; \
	fi
	$(PYTHON) -m black $(BACKEND_DIR)/app $(BACKEND_DIR)/tests
	$(PYTHON) -m ruff check --fix $(BACKEND_DIR) || true
	@echo "$(COLOR_GREEN)✓ 后端代码格式化完成$(COLOR_RESET)"

format-frontend: ## 格式化前端代码
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)格式化前端代码...$(COLOR_RESET)"
	@cd $(FRONTEND_DIR) && npm run format
	@echo "$(COLOR_GREEN)✓ 前端代码格式化完成$(COLOR_RESET)"

check: lint test ## 运行完整的代码检查和测试

# ============================================================================
# 清理
# ============================================================================

clean: clean-backend clean-frontend ## 清理构建文件和缓存

clean-backend: ## 清理后端构建文件
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)清理后端文件...$(COLOR_RESET)"
	@find $(BACKEND_DIR) -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type f -name "*.pyc" -delete 2>/dev/null || true
	@find $(BACKEND_DIR) -type f -name "*.pyo" -delete 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name ".pytest_cache" -exec rm -r {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name ".mypy_cache" -exec rm -r {} + 2>/dev/null || true
	@find $(BACKEND_DIR) -type d -name ".ruff_cache" -exec rm -r {} + 2>/dev/null || true
	@echo "$(COLOR_GREEN)✓ 后端文件清理完成$(COLOR_RESET)"

clean-frontend: ## 清理前端构建文件
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)清理前端文件...$(COLOR_RESET)"
	@rm -rf $(FRONTEND_DIR)/node_modules/.vite 2>/dev/null || true
	@rm -rf $(FRONTEND_DIR)/dist 2>/dev/null || true
	@rm -rf $(FRONTEND_DIR)/.vite 2>/dev/null || true
	@echo "$(COLOR_GREEN)✓ 前端文件清理完成$(COLOR_RESET)"

clean-all: clean ## 完全清理（包括依赖和虚拟环境）
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)完全清理...$(COLOR_RESET)"
	@rm -rf $(VENV) 2>/dev/null || true
	@rm -rf $(FRONTEND_DIR)/node_modules 2>/dev/null || true
	@rm -rf $(FRONTEND_DIR)/package-lock.json 2>/dev/null || true
	@rm -rf $(DATA_DIR)/*.db 2>/dev/null || true
	@rm -rf $(DATA_DIR)/*.db-journal 2>/dev/null || true
	@echo "$(COLOR_GREEN)✓ 完全清理完成$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)注意: 已删除虚拟环境和 node_modules，需要重新运行 make install$(COLOR_RESET)"

# ============================================================================
# 实用工具
# ============================================================================

logs-backend: ## 查看后端日志（如果使用 make dev 启动）
	@tail -f /tmp/backend.log 2>/dev/null || echo "后端日志文件不存在"

logs-frontend: ## 查看前端日志（如果使用 make dev 启动）
	@tail -f /tmp/frontend.log 2>/dev/null || echo "前端日志文件不存在"

logs-db: ## 查看数据库日志
	@cd $(ENV_DIR) && docker compose logs -f postgres mysql

status: ## 查看服务状态
	@echo "$(COLOR_BOLD)$(COLOR_BLUE)服务状态:$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BOLD)后端服务:$(COLOR_RESET)"
	@pgrep -f "uvicorn app.main:app" > /dev/null && echo "  $(COLOR_GREEN)✓ 运行中$(COLOR_RESET)" || echo "  $(COLOR_YELLOW)✗ 未运行$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BOLD)前端服务:$(COLOR_RESET)"
	@pgrep -f "vite" > /dev/null && echo "  $(COLOR_GREEN)✓ 运行中$(COLOR_RESET)" || echo "  $(COLOR_YELLOW)✗ 未运行$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BOLD)数据库服务:$(COLOR_RESET)"
	@cd $(ENV_DIR) && docker compose ps postgres mysql 2>/dev/null || echo "  $(COLOR_YELLOW)未运行$(COLOR_RESET)"
