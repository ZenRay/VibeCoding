#!/bin/bash
# 测试 ca-cli 编译

set -e

echo "🔨 开始编译 ca-cli..."
cd "$(dirname "$0")"

# 检查编译
echo "📋 检查编译..."
cargo check --package ca-cli --all-features

echo "✅ 编译检查成功！"
