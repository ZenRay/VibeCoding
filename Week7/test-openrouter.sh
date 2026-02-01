#!/bin/bash

# 测试 OpenRouter 配置

set -e

echo "🧪 测试 OpenRouter 配置"
echo "========================"
echo ""

cd backend

# 激活虚拟环境
if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "❌ 虚拟环境不存在"
    exit 1
fi

# 加载配置
if [ -f ".env" ]; then
    export $(grep "^AI_PROVIDER=" .env | xargs) 2>/dev/null || true
    export $(grep "^OPENROUTER_API_KEY=" .env | xargs) 2>/dev/null || true
    export $(grep "^OPENROUTER_MODEL=" .env | xargs) 2>/dev/null || true
fi

echo "📋 当前配置:"
echo "   AI_PROVIDER:        ${AI_PROVIDER:-未设置}"
echo "   OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:0:20}..."
echo "   OPENROUTER_MODEL:   ${OPENROUTER_MODEL:-未设置}"
echo ""

if [ "$AI_PROVIDER" != "openrouter" ]; then
    echo "⚠️  AI_PROVIDER 不是 'openrouter'"
    echo "   请在 .env 中设置: AI_PROVIDER=openrouter"
    exit 1
fi

if [ -z "$OPENROUTER_API_KEY" ]; then
    echo "❌ OPENROUTER_API_KEY 未设置"
    echo "   请在 .env 中设置你的 OpenRouter API Key"
    echo "   获取 Key: https://openrouter.ai/keys"
    exit 1
fi

echo "🔍 测试 1: 验证 OpenRouter API 连接..."
python3 << 'EOF'
import httpx
import os

api_key = os.getenv("OPENROUTER_API_KEY")

try:
    client = httpx.Client(
        base_url="https://openrouter.ai/api/v1",
        headers={
            "Authorization": f"Bearer {api_key}",
        },
        timeout=10
    )
    
    # 测试 API 连接（获取模型列表）
    response = client.get("/models")
    
    if response.status_code == 200:
        print("   ✅ OpenRouter API 连接成功")
        data = response.json()
        print(f"   可用模型数量: {len(data.get('data', []))}")
    else:
        print(f"   ❌ API 连接失败: {response.status_code}")
        print(f"   响应: {response.text[:200]}")
        exit(1)
    
    client.close()
except Exception as e:
    print(f"   ❌ 连接失败: {e}")
    exit(1)
EOF
echo ""

echo "🔍 测试 2: 检查 Gemini 图像模型是否可用..."
python3 << 'EOF'
import httpx
import os

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash-image")

try:
    client = httpx.Client(
        base_url="https://openrouter.ai/api/v1",
        headers={
            "Authorization": f"Bearer {api_key}",
        },
        timeout=10
    )
    
    response = client.get("/models")
    
    if response.status_code == 200:
        data = response.json()
        models = [m['id'] for m in data.get('data', [])]
        
        if model in models:
            print(f"   ✅ 模型 {model} 可用")
        else:
            print(f"   ⚠️  模型 {model} 不在可用列表中")
            print("   可用的 Gemini 图像模型:")
            gemini_models = [m for m in models if 'gemini' in m.lower() and 'image' in m.lower()]
            for gm in gemini_models[:5]:
                print(f"     - {gm}")
    
    client.close()
except Exception as e:
    print(f"   ❌ 检查失败: {e}")
    exit(1)
EOF
echo ""

echo "🔍 测试 3: 测试简单图像生成..."
python3 << 'EOF'
import httpx
import os

api_key = os.getenv("OPENROUTER_API_KEY")
model = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash-image")

try:
    client = httpx.Client(
        base_url="https://openrouter.ai/api/v1",
        headers={
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/vibecoding/ai-slide-generator",
            "X-Title": "AI Slide Generator Test"
        },
        timeout=60
    )
    
    print(f"   使用模型: {model}")
    print("   生成测试图像...")
    
    response = client.post(
        "/chat/completions",
        json={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Generate a simple red circle on white background"}
                    ]
                }
            ],
            "modalities": ["image", "text"]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        if 'choices' in data and len(data['choices']) > 0:
            message = data['choices'][0]['message']
            has_image = any(
                isinstance(c, dict) and c.get('type') == 'image_url' 
                for c in message.get('content', [])
            )
            if has_image:
                print("   ✅ 图像生成成功!")
            else:
                print("   ⚠️  响应中没有图像")
                print(f"   响应内容: {message.get('content', [])}")
        else:
            print("   ⚠️  响应格式异常")
            print(f"   响应: {data}")
    else:
        print(f"   ❌ API 调用失败: {response.status_code}")
        print(f"   响应: {response.text[:500]}")
        exit(1)
    
    client.close()
except Exception as e:
    print(f"   ❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
EOF
echo ""

echo "✅ 所有测试完成!"
echo ""
echo "💡 下一步:"
echo "   1. 重启后端: ./stop-backend.sh && ./start-backend.sh"
echo "   2. 在前端点击'初始化风格'测试生图功能"
echo ""
echo "📚 参考文档:"
echo "   - OpenRouter 官网: https://openrouter.ai/"
echo "   - API 文档: https://openrouter.ai/docs"
echo "   - 模型列表: https://openrouter.ai/models"
