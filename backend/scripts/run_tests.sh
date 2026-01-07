#!/bin/bash
# 运行测试脚本

set -e

echo "=========================================="
echo "运行 Project Alpha 后端测试"
echo "=========================================="
echo ""

cd "$(dirname "$0")/.."

# 检查是否在虚拟环境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  未检测到虚拟环境，建议先激活虚拟环境"
    echo "   source .venv/bin/activate"
    echo ""
fi

# 运行测试
echo "🧪 运行所有测试..."
pytest -v

echo ""
echo "=========================================="
echo "✅ 测试完成！"
echo "=========================================="
