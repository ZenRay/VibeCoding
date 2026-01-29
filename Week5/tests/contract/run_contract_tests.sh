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
#   - L1: 基础查询（15个用例）- 通过率 86.7% ✅
#   - L2: 多表关联（15个用例）- 通过率 80.0% ✅
#   - L3: 聚合分析（12个用例）- 通过率 41.7% 🟡
#   - L4: 复杂逻辑（10个用例）- 通过率 40.0% 🟡
#   - L5: 高级特性（8个用例）- 通过率 0% 🔴
#   - S1: 安全测试（10个用例）- 通过率 10% 🔴
#   总计：70个测试用例
#
# 使用方法：
# ---------
#   cd /path/to/Week5/tests/contract
#   ./run_contract_tests.sh [mode]
#
# 模式参数：
#   sample   - 运行样例测试（3个用例，快速验证）【默认】
#   full     - 运行完整测试（70个用例，约4-5分钟）
#   core     - 仅测试核心模块 L1+L2（30个用例，约2分钟）✨ NEW
#   weak     - 仅测试弱项模块 L3+L4+L5+S1（40个用例，约3分钟）✨ NEW
#   l1       - 仅测试 L1 基础查询（15个用例，约1分钟）
#   l2       - 仅测试 L2 多表关联（15个用例，约1分钟）
#   l3       - 仅测试 L3 聚合分析（12个用例，约1分钟）
#   l4       - 仅测试 L4 复杂逻辑（10个用例，约45秒）
#   l5       - 仅测试 L5 高级特性（8个用例，约30秒）
#   s1       - 仅测试 S1 安全测试（10个用例，约45秒）
#
# 推荐用法：
# ---------
#   # 快速验证基本功能
#   ./run_contract_tests.sh sample
#
#   # 验证核心功能（L1+L2 已达标）
#   ./run_contract_tests.sh core
#
#   # 专注优化弱项（L3-S1 需要提升）
#   ./run_contract_tests.sh weak
#
#   # 单独测试某个模块
#   ./run_contract_tests.sh l3
#
# 示例：
#   ./run_contract_tests.sh               # 运行样例测试
#   ./run_contract_tests.sh weak          # 仅测试 L3+L4+L5+S1
#   ./run_contract_tests.sh l3            # 仅测试 L3 聚合分析
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
    core)
        echo "🧪 Running CORE module tests (L1 + L2 = 30 test cases)..."
        echo "📊 Current pass rate: L1 86.7%, L2 80.0% → Combined 83.3% ✅"
        echo "⏱️  Estimated time: ~2 minutes"
        echo ""
        python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from tests.contract.run_tests_module import run_selected_modules
asyncio.run(run_selected_modules(['L1', 'L2']))
" 2>&1 | tee /tmp/contract_test_results_core.txt
        ;;
    weak)
        echo "🧪 Running WEAK module tests (L3 + L4 + L5 + S1 = 40 test cases)..."
        echo "📊 Current pass rate: L3 41.7%, L4 40%, L5 0%, S1 10% → Combined 22.5% 🟡"
        echo "⏱️  Estimated time: ~3 minutes"
        echo ""
        python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from tests.contract.run_tests_module import run_selected_modules
asyncio.run(run_selected_modules(['L3', 'L4', 'L5', 'S1']))
" 2>&1 | tee /tmp/contract_test_results_weak.txt
        ;;
    l1)
        echo "🧪 Running L1 Basic Query tests (15 test cases)..."
        echo "📊 Current pass rate: 86.7% (13/15) ✅"
        echo "⏱️  Estimated time: ~1 minute"
        echo ""
        python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from tests.contract.run_tests_module import run_selected_modules
asyncio.run(run_selected_modules(['L1']))
" 2>&1 | tee /tmp/contract_test_results_l1.txt
        ;;
    l2)
        echo "🧪 Running L2 Multi-Table JOIN tests (15 test cases)..."
        echo "📊 Current pass rate: 80.0% (12/15) ✅"
        echo "⏱️  Estimated time: ~1 minute"
        echo ""
        python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from tests.contract.run_tests_module import run_selected_modules
asyncio.run(run_selected_modules(['L2']))
" 2>&1 | tee /tmp/contract_test_results_l2.txt
        ;;
    l3)
        echo "🧪 Running L3 Aggregation tests (12 test cases)..."
        echo "📊 Current pass rate: 41.7% (5/12) 🟡"
        echo "⏱️  Estimated time: ~1 minute"
        echo ""
        python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from tests.contract.run_tests_module import run_selected_modules
asyncio.run(run_selected_modules(['L3']))
" 2>&1 | tee /tmp/contract_test_results_l3.txt
        ;;
    l4)
        echo "🧪 Running L4 Complex Logic tests (10 test cases)..."
        echo "📊 Current pass rate: 40.0% (4/10) 🟡"
        echo "⏱️  Estimated time: ~45 seconds"
        echo ""
        python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from tests.contract.run_tests_module import run_selected_modules
asyncio.run(run_selected_modules(['L4']))
" 2>&1 | tee /tmp/contract_test_results_l4.txt
        ;;
    l5)
        echo "🧪 Running L5 Advanced Features tests (8 test cases)..."
        echo "📊 Current pass rate: 0% (0/8) 🔴"
        echo "⏱️  Estimated time: ~30 seconds"
        echo ""
        python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from tests.contract.run_tests_module import run_selected_modules
asyncio.run(run_selected_modules(['L5']))
" 2>&1 | tee /tmp/contract_test_results_l5.txt
        ;;
    s1)
        echo "🧪 Running S1 Security tests (10 test cases)..."
        echo "📊 Current pass rate: 10% (1/10) 🔴"
        echo "⏱️  Estimated time: ~45 seconds"
        echo ""
        python -c "
import asyncio
import sys
sys.path.insert(0, '.')
from tests.contract.run_tests_module import run_selected_modules
asyncio.run(run_selected_modules(['S1']))
" 2>&1 | tee /tmp/contract_test_results_s1.txt
        ;;
    *)
        echo "❌ Error: Invalid argument '$TEST_MODE'"
        echo ""
        echo "Usage: $0 [mode]"
        echo ""
        echo "Available modes:"
        echo "  sample   - Quick validation (3 test cases, ~15s) [DEFAULT]"
        echo "  full     - All tests (70 test cases, ~5min)"
        echo ""
        echo "  core     - Core modules L1+L2 (30 test cases, ~2min) ✨"
        echo "  weak     - Weak modules L3+L4+L5+S1 (40 test cases, ~3min) ✨"
        echo ""
        echo "  l1       - L1 Basic Query only (15 test cases, ~1min)"
        echo "  l2       - L2 Multi-Table JOIN only (15 test cases, ~1min)"
        echo "  l3       - L3 Aggregation only (12 test cases, ~1min)"
        echo "  l4       - L4 Complex Logic only (10 test cases, ~45s)"
        echo "  l5       - L5 Advanced Features only (8 test cases, ~30s)"
        echo "  s1       - S1 Security only (10 test cases, ~45s)"
        echo ""
        echo "Examples:"
        echo "  $0              # Quick validation"
        echo "  $0 core         # Test L1+L2 (core functionality)"
        echo "  $0 weak         # Test L3+L4+L5+S1 (areas needing improvement)"
        echo "  $0 l3           # Test only L3 aggregation"
        exit 1
        ;;
esac

echo ""
echo "✅ Test execution complete!"
echo "📄 Results saved to /tmp/contract_test_results_*.txt"
