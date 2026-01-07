#!/usr/bin/env python3
"""自动修复前端格式问题（模拟 Prettier 规则）"""

import os
import re
from pathlib import Path


def fix_file(file_path):
    """修复单个文件的格式"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. 去除行尾空格
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]

    # 2. 确保文件以换行符结尾（但只有一个）
    while lines and not lines[-1]:
        lines.pop()
    if lines:
        lines.append('')

    content = '\n'.join(lines)

    # 3. 去除多余的空行（连续超过2个空行）
    content = re.sub(r'\n\n\n+', '\n\n', content)

    # 如果内容改变，写回文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    """主函数"""
    script_dir = Path(__file__).parent
    frontend_dir = script_dir / 'frontend' / 'src'

    if not frontend_dir.exists():
        print(f"❌ 前端目录不存在: {frontend_dir}")
        return 1

    print("🎨 修复前端格式问题...")
    print(f"目录: {frontend_dir}")
    print("")

    fixed_count = 0
    total_count = 0

    # 遍历所有 TypeScript 和 CSS 文件
    for ext in ['**/*.ts', '**/*.tsx', '**/*.css']:
        for file_path in frontend_dir.glob(ext):
            total_count += 1
            if fix_file(file_path):
                fixed_count += 1
                rel_path = file_path.relative_to(frontend_dir)
                print(f"  ✓ {rel_path}")

    print("")
    print(f"✅ 完成！修复了 {fixed_count}/{total_count} 个文件")
    print("")

    if fixed_count > 0:
        print("请运行以下命令提交:")
        print("  git add -A")
        print("  git commit -m 'style: 修复前端格式（去除行尾空格、规范换行符）'")
        print("  git push origin main")
        return 0
    else:
        print("没有需要修复的文件")
        return 0


if __name__ == '__main__':
    exit(main())
