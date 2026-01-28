#!/bin/bash
#
# ============================================================================
# Contract Test Runner Script for PostgreSQL MCP Server
# ============================================================================
#
# 用途说明：
# ---------
# 本脚本用于运行 PostgreSQL MCP 服务器的契约测试（Contract Tests），
# 验证自然语言到 SQL 的转换准确性。
#
# 契约测试覆盖：
#   - L1: 基础查询（15个用例）
#   - L2: 多表关联（15个用例）
#   - L3: 聚合分析（12个用例）
#   - L4: 复杂逻辑（10个用例）
#   - L5: 高级特性（8个用例）
#   - S1: 安全测试（10个用例）
#   总计：70个测试用例
#
# 使用方法：
# ---------
#   cd /path/to/Week5/tests/contract
#   ./run_contract_tests.sh [sample|full]
#
# 参数：
#   sample - 运行样例测试（3个用例，快速验证）【默认】
#   full   - 运行完整测试（70个用例，约4-5分钟）
#
# 示例：
#   ./run_contract_tests.sh               # 运行样例测试
#   ./run_contract_tests.sh sample        # 运行样例测试
#   ./run_contract_tests.sh full          # 运行完整测试
#
# 环境要求：
# ---------
#   1. PostgreSQL 测试数据库已启动（docker compose up -d）
#   2. 虚拟环境已创建（Week5/.venv）
#   3. OpenAI API 已配置（config/config.yaml）
#
# 注意事项：
# ---------
#   - 脚本会自动禁用代理设置以避免 API 连接问题
#   - 测试结果保存在 /tmp/contract_test_results_*.txt
#   - 完整测试因 API 频率限制需要 4-5 分钟
#
# ============================================================================

set -e  # Exit on error

# Navigate to project root (Week5/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$PROJECT_ROOT"

echo "📁 Project root: $PROJECT_ROOT"
echo ""

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ Error: Virtual environment not found at $PROJECT_ROOT/.venv/"
    echo "   Please create it first: python -m venv .venv"
    exit 1
fi

# Set database password
export TEST_DB_PASSWORD="${TEST_DB_PASSWORD:-testpass123}"
echo "✅ Database password set"

# Disable proxy settings for API connections
# These can interfere with OpenAI-compatible API endpoints
unset HTTP_PROXY
unset HTTPS_PROXY
unset ALL_PROXY
unset http_proxy
unset https_proxy
unset all_proxy

# Keep NO_PROXY for local services
export NO_PROXY="localhost,127.0.0.1"
echo "✅ Proxy settings cleared for API connections"
echo ""

# Determine which test to run
TEST_MODE="${1:-sample}"

case "$TEST_MODE" in
    sample)
        echo "🧪 Running SAMPLE contract tests (3 test cases from L1)..."
        echo "⏱️  Estimated time: ~15 seconds"
        echo ""
        python -m tests.contract.run_tests_sample 2>&1 | tee /tmp/contract_test_results_sample.txt
        ;;
    full)
        echo "🧪 Running FULL contract tests (70 test cases: L1-L5 + S1)..."
        echo "⚠️  This will take approximately 4-5 minutes due to API rate limiting."
        echo "   - Request delay: 1.5s per test case"
        echo "   - Batch delay: 5s between categories"
        echo ""
        python -m tests.contract.run_tests 2>&1 | tee /tmp/contract_test_results_full.txt
        ;;
    *)
        echo "❌ Error: Invalid argument '$TEST_MODE'"
        echo ""
        echo "Usage: $0 [sample|full]"
        echo ""
        echo "Arguments:"
        echo "  sample - Run 3 sample test cases (default)"
        echo "  full   - Run all 70 test cases"
        exit 1
        ;;
esac

echo ""
echo "✅ Test execution complete!"
echo "📄 Results saved to /tmp/contract_test_results_*.txt"
