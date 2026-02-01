#!/bin/bash

# 测试代理配置是否正常工作

set -e

echo "🧪 测试代理配置"
echo "=================="
echo ""

cd backend

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ 虚拟环境不存在"
    exit 1
fi

# 加载代理配置
if [ -f ".env" ]; then
    export $(grep "^HTTP_PROXY=" .env | xargs) 2>/dev/null || true
    export $(grep "^HTTPS_PROXY=" .env | xargs) 2>/dev/null || true
    export $(grep "^NO_PROXY=" .env | xargs) 2>/dev/null || true
fi

echo "📋 当前代理配置:"
echo "   HTTP_PROXY:  ${HTTP_PROXY:-未设置}"
echo "   HTTPS_PROXY: ${HTTPS_PROXY:-未设置}"
echo "   NO_PROXY:    ${NO_PROXY:-未设置}"
echo ""

echo "🔍 测试 1: 检查代理端口是否开放..."
if nc -z 127.0.0.1 7890 2>/dev/null; then
    echo "   ✅ 代理端口 7890 正常监听"
else
    echo "   ❌ 代理端口 7890 未开放"
    echo "   提示: 请确保代理软件（Clash/V2Ray）正在运行"
    exit 1
fi
echo ""

echo "🔍 测试 2: 通过代理访问 Google..."
python3 << 'EOF'
import httpx
import os

proxy = os.getenv("HTTPS_PROXY")
if not proxy:
    print("   ❌ HTTPS_PROXY 环境变量未设置")
    exit(1)

print(f"   使用代理: {proxy}")

try:
    # 测试访问 Google (httpx 会自动使用环境变量中的代理)
    with httpx.Client(timeout=10) as client:
        resp = client.get("https://www.google.com")
        print(f"   ✅ Google 访问成功 (状态码: {resp.status_code})")
except Exception as e:
    print(f"   ❌ Google 访问失败: {e}")
    exit(1)
EOF
echo ""

echo "🔍 测试 3: 通过代理访问 Gemini API..."
python3 << 'EOF'
import httpx
import os

proxy = os.getenv("HTTPS_PROXY")

try:
    # 测试访问 Gemini API 端点 (httpx 会自动使用环境变量中的代理)
    with httpx.Client(timeout=10) as client:
        resp = client.get("https://generativelanguage.googleapis.com")
        print(f"   ✅ Gemini API 访问成功 (状态码: {resp.status_code})")
except Exception as e:
    print(f"   ❌ Gemini API 访问失败: {e}")
    exit(1)
EOF
echo ""

echo "🔍 测试 4: 测试完整的 Gemini 图像生成 API..."
python3 << 'EOF'
import os
from google import genai

proxy = os.getenv("HTTPS_PROXY")
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    # 从 .env 读取
    with open(".env") as f:
        for line in f:
            if line.startswith("GEMINI_API_KEY="):
                api_key = line.split("=", 1)[1].strip()
                break

if not api_key:
    print("   ❌ GEMINI_API_KEY 未设置")
    exit(1)

# 设置环境变量
os.environ['GOOGLE_API_KEY'] = api_key

try:
    print(f"   使用代理: {proxy}")
    print(f"   API Key: {api_key[:20]}...")
    
    # 初始化客户端（会自动使用环境变量中的代理）
    client = genai.Client()
    print("   ✅ Gemini 客户端初始化成功")
    
    # 尝试生成简单的文本图像（最小化配额消耗）
    response = client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents="A simple red circle on white background"
    )
    print("   ✅ 图像生成 API 调用成功!")
    print(f"   返回内容数: {len(response.parts)}")
    
except Exception as e:
    error_str = str(e)
    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
        print("   ⚠️  配额已用尽（但代理工作正常！）")
        print("   提示: 等待配额重置或升级到付费账户")
    elif "403" in error_str or "PERMISSION_DENIED" in error_str:
        print("   ❌ API Key 权限不足或无效")
    else:
        print(f"   ❌ API 调用失败: {e}")
        exit(1)
EOF
echo ""

echo "✅ 所有测试完成!"
echo ""
echo "💡 如果测试失败，请检查:"
echo "   1. 代理软件（Clash/V2Ray）是否正在运行"
echo "   2. 代理端口是否正确（默认 7890）"
echo "   3. 代理是否允许访问 Google 服务"
echo "   4. API Key 是否有效且有配额"
