#!/usr/bin/env python3
"""批量修复前端 Prettier 格式问题"""

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
    content = '\n'.join(lines)

    # 2. 确保文件以换行符结尾
    if content and not content.endswith('\n'):
        content += '\n'

    # 3. 去除多余的空行（连续超过2个空行）
    content = re.sub(r'\n{3,}', '\n\n', content)

    # 4. 移除分号（如果 Prettier 配置是 semi: false）
    # 注意：不要移除字符串中的分号
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # 只处理代码行，不处理注释和字符串
        if not line.strip().startswith('//') and not line.strip().startswith('*'):
            # 简单处理：移除行尾的分号（但保留语句中的分号）
            if line.rstrip().endswith(';'):
                lines[i] = line.rstrip()[:-1]
    content = '\n'.join(lines)

    # 如果内容改变，写回文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    """主函数"""
    frontend_dir = Path(__file__).parent.parent / 'frontend' / 'src'

    if not frontend_dir.exists():
        print(f"❌ 前端目录不存在: {frontend_dir}")
        return

    fixed_count = 0
    total_count = 0

    # 遍历所有 TypeScript 和 CSS 文件
    for ext in ['**/*.ts', '**/*.tsx', '**/*.css']:
        for file_path in frontend_dir.glob(ext):
            total_count += 1
            if fix_file(file_path):
                fixed_count += 1
                print(f"✓ 修复: {file_path.relative_to(frontend_dir.parent)}")

    print(f"\n完成！修复了 {fixed_count}/{total_count} 个文件")


if __name__ == '__main__':
    main()
