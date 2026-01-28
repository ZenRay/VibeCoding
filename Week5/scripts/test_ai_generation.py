#!/usr/bin/env python3
"""
AI SQL 生成测试 - 通义千问 (Qwen)

测试 AI 是否能正确生成 SQL 查询
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from postgres_mcp.config import Config
from postgres_mcp.ai.openai_client import OpenAIClient
from postgres_mcp.db.schema_inspector import SchemaInspector
from postgres_mcp.core.sql_validator import SQLValidator


async def test_ai_generation():
    """测试 AI SQL 生成"""
    print("=" * 80)
    print("🤖 AI SQL 生成测试 - 通义千问 (Qwen)")
    print("=" * 80)
    print()

    # 1. 加载配置
    print("📋 加载配置...")
    config = Config.load("config/config.yaml")
    print(f"   ✅ AI 模型: {config.openai.model}")
    print(f"   ✅ Base URL: {config.openai.base_url}")
    print()

    # 2. 初始化 AI 客户端
    print("🤖 初始化 AI 客户端...")
    ai_client = OpenAIClient(
        api_key=config.openai.resolved_api_key,
        model=config.openai.model,
        temperature=config.openai.temperature,
        max_tokens=config.openai.max_tokens,
        timeout=config.openai.timeout,
        base_url=config.openai.base_url,
    )
    print("   ✅ AI 客户端初始化成功")
    print()

    # 3. 初始化 SQL 验证器
    sql_validator = SQLValidator()

    # 4. 加载测试示例
    examples_file = Path("examples/sample_queries.json")
    if not examples_file.exists():
        print(f"   ❌ 示例文件不存在: {examples_file}")
        return

    with open(examples_file) as f:
        data = json.load(f)

    # 5. 测试前8个示例（不同难度）
    examples = data["examples"][:8]
    print(f"🧪 测试 {len(examples)} 个示例查询:")
    print("-" * 80)
    print()

    success_count = 0
    results = []

    for i, example in enumerate(examples, 1):
        nl_query = example["natural_language"]
        db_name = example["database"]
        difficulty = example["difficulty"]
        category = example.get("category", "unknown")

        print(f"{i}. [{difficulty.upper()}/{category}]")
        print(f"   查询: {nl_query}")

        result = {
            "id": i,
            "query": nl_query,
            "database": db_name,
            "difficulty": difficulty,
            "category": category,
        }

        try:
            # 获取 Schema
            db_config = config.databases[db_name]
            inspector = SchemaInspector(
                host=db_config.host,
                port=db_config.port,
                user=db_config.user,
                password=db_config.password,
                database=db_config.database,
            )
            await inspector.connect()
            schema = await inspector.inspect_schema()
            await inspector.disconnect()

            # 生成 SQL
            sql = await ai_client.generate_sql(nl_query, schema)
            result["generated_sql"] = sql

            # 验证 SQL
            validation = sql_validator.validate(sql)
            result["valid"] = validation.valid

            if validation.valid:
                print(f"   ✅ 成功: {sql}")
                result["status"] = "success"
                success_count += 1
            else:
                print(f"   ⚠️  SQL 验证失败:")
                for error in validation.errors:
                    print(f"      - {error}")
                result["status"] = "validation_failed"
                result["errors"] = validation.errors

        except Exception as e:
            print(f"   ❌ 生成失败: {e}")
            result["status"] = "error"
            result["error"] = str(e)

        results.append(result)
        print()

    # 6. 总结
    print("=" * 80)
    print("📊 测试总结")
    print("=" * 80)
    print()
    print(f"总测试数: {len(examples)}")
    print(f"成功: {success_count}")
    print(f"失败: {len(examples) - success_count}")
    print(f"成功率: {success_count/len(examples)*100:.1f}%")
    print()

    # 按难度统计
    by_difficulty = {}
    for r in results:
        diff = r["difficulty"]
        if diff not in by_difficulty:
            by_difficulty[diff] = {"total": 0, "success": 0}
        by_difficulty[diff]["total"] += 1
        if r["status"] == "success":
            by_difficulty[diff]["success"] += 1

    print("按难度统计:")
    for diff in ["easy", "medium", "hard"]:
        if diff in by_difficulty:
            stats = by_difficulty[diff]
            rate = stats["success"] / stats["total"] * 100
            print(f"  {diff.upper()}: {stats['success']}/{stats['total']} ({rate:.0f}%)")

    print()
    print("=" * 80)

    # 7. 保存结果
    output_file = "test_results_ai_generation.json"
    with open(output_file, "w") as f:
        json.dump({
            "model": config.openai.model,
            "base_url": config.openai.base_url,
            "total": len(examples),
            "success": success_count,
            "success_rate": f"{success_count/len(examples)*100:.1f}%",
            "by_difficulty": by_difficulty,
            "results": results,
        }, f, indent=2, ensure_ascii=False)

    print(f"📄 详细结果已保存到: {output_file}")


if __name__ == "__main__":
    asyncio.run(test_ai_generation())
