# MCP 服务器稳定性问题诊断

## 🔴 主要问题

**MCP 服务器频繁崩溃/退出**

### 症状
1. 第一个查询（list_databases）成功 ✅
2. 后续查询时服务器已经不在运行 ❌
3. Claude 卡在"思考"阶段（1-3分钟）
4. 最终无响应或超时

---

## 🔍 根本原因分析

### 可能原因 1: 超时问题
- OpenAI API timeout: 30 秒
- 通义千问响应可能较慢
- 超时后服务器可能崩溃

### 可能原因 2: 错误处理
- AI API 调用失败
- 没有正确捕获异常
- 导致服务器退出

### 可能原因 3: Claude 通信问题
- stdio 管道断开
- Claude 重连时服务器已退出
- 需要更好的重连机制

---

## 🔧 建议修复

### 方案 1: 增加超时时间（立即）

修改 `config.yaml`:
```yaml
openai:
  timeout: 60.0  # 从 30 改为 60 秒
```

### 方案 2: 添加重试逻辑

在 `openai_client.py` 中添加重试：
```python
async def generate(...):
    for attempt in range(3):
        try:
            response = await self._client.chat.completions.create(...)
            return response
        except timeout:
            if attempt < 2:
                await asyncio.sleep(2)
                continue
            raise
```

### 方案 3: 改进错误处理

确保所有 MCP 工具都有 try-catch：
```python
@server.call_tool()
async def call_tool(name, arguments):
    try:
        # ... 处理逻辑
    except Exception as e:
        logger.error("tool_failed", tool=name, error=str(e))
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}"
        )]
```

### 方案 4: 使用 systemd/supervisor

创建一个守护进程自动重启：
```bash
# 使用 while true 循环
while true; do
    python -m postgres_mcp
    echo "MCP crashed, restarting in 2s..."
    sleep 2
done
```

---

## 🎯 临时解决方案（立即可用）

### 方案 A: 每次查询前重启（最简单）

```bash
# 在 Claude 中，每个查询前：
/exit
claude
# 然后再查询
```

### 方案 B: 使用直接 SQL（绕过 AI）

不生成 SQL，直接执行已知的安全 SQL：
```
请执行这个 SQL：
SELECT * FROM products LIMIT 5;
数据库：ecommerce_small
```

### 方案 C: 测试不需要 AI 的工具

```
使用 list_databases 工具
```

---

## 📊 测试建议

鉴于当前稳定性问题，建议：

### 优先级 1: 验证基础功能
- [x] list_databases ✅ 已验证
- [ ] 直接执行 SQL（不生成）
- [ ] SQL 验证（不调用 AI）

### 优先级 2: AI 功能（需要修复）
- [ ] SQL 生成（通义千问）
- [ ] 复杂查询
- [ ] 自然语言理解

### 优先级 3: 高级功能
- [ ] Resources
- [ ] Schema 查询
- [ ] 查询历史

---

## 🚨 当前状态总结

| 组件 | 状态 | 说明 |
|------|------|------|
| MCP 服务器启动 | ✅ | 能正常启动 |
| 数据库连接 | ✅ | 6 个连接正常 |
| Schema 缓存 | ✅ | 30 个表加载 |
| Claude 连接 | ✅ | 能建立连接 |
| list_databases | ✅ | 第一个查询成功 |
| **服务器稳定性** | ❌ | **频繁崩溃** |
| AI SQL 生成 | ❌ | 未能完成测试 |
| 查询执行 | ❌ | 未能完成测试 |

**核心问题**: 服务器在第一个查询后就不稳定了

---

## 💡 建议下一步

1. **修改 timeout**：将 `config.yaml` 中的 timeout 改为 60 秒
2. **简化测试**：只测试不需要 AI 的功能
3. **考虑重构**：添加更好的错误处理和重试逻辑

或者：

**暂时跳过 Claude 测试**，直接写单元测试验证核心功能！

---

## 📝 测试报告草稿

**测试日期**: 2026-01-29  
**测试环境**: Week5 MCP Server + Claude CLI  
**测试结果**: 

✅ **部分成功**:
- MCP 服务器代码修复完成
- 能够启动并建立连接
- list_databases 工具验证成功

❌ **失败**:
- 服务器稳定性问题
- 无法完成完整功能测试
- AI 功能未能验证

**建议**: 优先修复稳定性问题，然后继续测试
