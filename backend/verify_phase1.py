#!/usr/bin/env python3
"""阶段 1 验证脚本

用于验证阶段 1 的所有组件是否正常工作
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))


def check_imports():
    """检查所有模块是否可以正常导入"""
    print("🔍 检查模块导入...")

    try:
        from app import __version__

        print(f"  ✅ app 模块导入成功 (版本: {__version__})")
    except Exception as e:
        print(f"  ❌ app 模块导入失败: {e}")
        return False

    try:
        from app.config import settings

        print("  ✅ config 模块导入成功")
        print(f"     - 数据库 URL: {settings.database_url[:50]}...")
    except Exception as e:
        print(f"  ❌ config 模块导入失败: {e}")
        return False

    try:
        print("  ✅ database 模块导入成功")
    except Exception as e:
        print(f"  ❌ database 模块导入失败: {e}")
        return False

    try:
        print("  ✅ models 模块导入成功")
        print("     - Ticket, Tag, TicketTag 模型已导入")
    except Exception as e:
        print(f"  ❌ models 模块导入失败: {e}")
        return False

    try:
        print("  ✅ schemas 模块导入成功")
    except Exception as e:
        print(f"  ❌ schemas 模块导入失败: {e}")
        return False

    try:
        print("  ✅ utils 模块导入成功")
    except Exception as e:
        print(f"  ❌ utils 模块导入失败: {e}")
        return False

    return True


def check_database_connection():
    """检查数据库连接"""
    print("\n🔍 检查数据库连接...")

    try:
        from app.database import engine

        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("  ✅ 数据库连接成功")
            return True
    except Exception as e:
        print(f"  ❌ 数据库连接失败: {e}")
        print("     请确保 PostgreSQL 已启动，并且数据库连接配置正确")
        return False


def check_tables():
    """检查数据库表是否存在"""
    print("\n🔍 检查数据库表...")

    try:
        from sqlalchemy import inspect

        from app.database import engine

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        required_tables = ["tickets", "tags", "ticket_tags"]
        missing_tables = [t for t in required_tables if t not in tables]

        if missing_tables:
            print(f"  ❌ 缺少表: {', '.join(missing_tables)}")
            print("     请运行: alembic upgrade head")
            return False
        else:
            print(f"  ✅ 所有必需的表都存在: {', '.join(required_tables)}")
            return True
    except Exception as e:
        print(f"  ❌ 检查表失败: {e}")
        return False


def check_triggers():
    """检查数据库触发器是否存在"""
    print("\n🔍 检查数据库触发器...")

    try:
        from app.database import engine

        with engine.connect() as conn:
            # 检查触发器函数
            result = conn.execute(
                """
                SELECT proname
                FROM pg_proc
                WHERE proname IN (
                    'update_updated_at_column',
                    'set_completed_at',
                    'normalize_tag_name'
                )
            """
            )
            functions = [row[0] for row in result]

            required_functions = [
                "update_updated_at_column",
                "set_completed_at",
                "normalize_tag_name",
            ]
            missing_functions = [f for f in required_functions if f not in functions]

            if missing_functions:
                print(f"  ⚠️  缺少触发器函数: {', '.join(missing_functions)}")
                print("     请运行: alembic upgrade head")
                return False
            else:
                print("  ✅ 所有触发器函数都存在")
                return True
    except Exception as e:
        print(f"  ❌ 检查触发器失败: {e}")
        return False


def check_fastapi_app():
    """检查 FastAPI 应用是否可以创建"""
    print("\n🔍 检查 FastAPI 应用...")

    try:
        from app.main import app

        print("  ✅ FastAPI 应用创建成功")
        print(f"     - 标题: {app.title}")
        print(f"     - 版本: {app.version}")
        print(f"     - Swagger UI: {app.docs_url}")
        print(f"     - ReDoc: {app.redoc_url}")
        return True
    except Exception as e:
        print(f"  ❌ FastAPI 应用创建失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("阶段 1 验证脚本")
    print("=" * 60)

    results = []

    # 检查模块导入
    results.append(("模块导入", check_imports()))

    # 检查数据库连接
    db_connected = check_database_connection()
    results.append(("数据库连接", db_connected))

    if db_connected:
        # 检查表
        results.append(("数据库表", check_tables()))

        # 检查触发器
        results.append(("数据库触发器", check_triggers()))

    # 检查 FastAPI 应用
    results.append(("FastAPI 应用", check_fastapi_app()))

    # 总结
    print("\n" + "=" * 60)
    print("验证结果总结")
    print("=" * 60)

    all_passed = True
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有检查通过！阶段 1 已完成。")
        print("\n下一步：")
        print("  1. 启动开发服务器: uvicorn app.main:app --reload")
        print("  2. 访问 Swagger UI: http://localhost:8000/docs")
        print("  3. 开始阶段 2：实现 API 端点")
    else:
        print("⚠️  部分检查未通过，请根据上述提示修复问题。")
        print("\n常见问题：")
        print("  - 数据库连接失败：检查 PostgreSQL 是否启动，.env 配置是否正确")
        print("  - 表不存在：运行 'alembic upgrade head'")
        print("  - 模块导入失败：确保虚拟环境已激活，依赖已安装")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
