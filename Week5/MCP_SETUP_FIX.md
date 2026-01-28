# MCP 配置说明

## 问题根源

Claude CLI 读取的是 **项目根目录** (`/home/ray/Documents/VibeCoding`) 的配置，
而不是子目录 (`Week5`) 的配置。

## 解决方案

配置文件已创建在正确位置：
```
/home/ray/Documents/VibeCoding/.claude/config.json
```

## 重要步骤

**必须重启 Claude** 才能读取新配置！

### 1. 退出当前 Claude 会话

在 Claude CLI 中输入：
```
/exit
```

或按 `Ctrl+D`

### 2. 重新启动 Claude

```bash
cd /home/ray/Documents/VibeCoding/Week5
claude
```

### 3. 验证 MCP 连接

在 Claude 中输入：
```
/mcp
```

应该看到：
```
✔ postgres-mcp · connected
```

## 快速测试

启动 Claude 后，直接测试：
```
请列出所有可用的数据库
```

预期返回 3 个数据库。

---

## 为什么是这个路径？

从终端输出可以看到：
```
Local MCPs (/home/ray/.claude.json [project: /home/ray/Documents/VibeCoding/Week5])
```

虽然当前在 Week5 目录，但 Claude 项目是 **VibeCoding** 根目录，
所以配置需要放在 `/home/ray/Documents/VibeCoding/.claude/config.json`
