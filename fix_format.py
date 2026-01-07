#!/usr/bin/env python3
"""修复前端格式问题"""

import os
import subprocess
from pathlib import Path

# 切换到 Week1 目录
os.chdir(Path(__file__).parent)

# 进入 frontend 目录
os.chdir('frontend')

print("🔧 安装依赖...")
result = subprocess.run(['npm', 'install'], capture_output=True, text=True)
if result.returncode != 0:
    print(f"⚠️  依赖已安装或安装失败: {result.stderr[:200]}")

print("\n🎨 运行 Prettier 格式化...")
result = subprocess.run(['npx', 'prettier', '--write', 'src/**/*.{ts,tsx,css}'],
                       capture_output=True, text=True, shell=False)

print(result.stdout)
if result.stderr:
    print(result.stderr)

if result.returncode == 0:
    print("\n✅ 格式化成功！")
    print("\n请运行以下命令提交:")
    print("  git add -A")
    print("  git commit -m 'style: 修复前端 Prettier 格式'")
    print("  git push origin main")
else:
    print(f"\n❌ 格式化失败: {result.returncode}")
