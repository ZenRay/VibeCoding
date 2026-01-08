# 下一阶段计划

**更新日期**：2026-01-09  
**当前进度**：92%（测试与优化已完成）  
**目标**：1 周内正式上线

---

## 📊 当前状态

### 已完成 ✅

| 阶段 | 内容 | 状态 |
|------|------|------|
| 阶段 0 | 环境准备 | ✅ 100% |
| 阶段 1 | 数据库与后端基础 | ✅ 100% |
| 阶段 2 | 后端 API 实现 | ✅ 100% |
| 阶段 3 | 前端基础设施 | ✅ 100% |
| 阶段 4 | 前端核心功能 | ✅ 100% |
| 阶段 4.5 | 环境和文档完善 | ✅ 100% |
| 阶段 5 | 前端扩展功能 | ✅ 100%（已完成） |
| 阶段 6 | 测试与优化 | 🟢 80%（覆盖率 82% + E2E） |

### 待完成 ⏳

| 阶段 | 内容 | 优先级 | 预估时间 |
|------|------|--------|----------|
| 阶段 6 | E2E 测试、性能优化 | ⭐⭐⭐⭐⭐ 最高 | 5 天 |
| 阶段 7 | 部署与上线 | ⭐⭐⭐⭐ 高 | 2-3 天 |

---

## 🎯 推荐执行计划

### Week 1：完成测试与优化

#### Day 1-2：E2E 测试

```bash
# 1. 安装 Playwright
cd frontend
npm install -D @playwright/test
npx playwright install chromium

# 2. 创建测试目录
mkdir -p tests/e2e

# 3. 编写核心测试用例
# - ticket-crud.spec.ts（创建/编辑/删除）
# - search-filter.spec.ts（搜索和过滤）
# - tag-management.spec.ts（标签管理）

# 4. 运行测试
npm run test:e2e
```

**验收标准**：
- ✅ 3 个核心流程测试通过
- ✅ 可在 Docker 中运行
- ✅ CI 集成完成

#### Day 3：性能优化

**前端优化**：
```typescript
// 1. React.memo 优化列表项
export const TicketListItem = React.memo(({ ticket }) => { ... })

// 2. useMemo 缓存过滤结果
const filteredTickets = useMemo(() => applyFilters(tickets, filters), [tickets, filters])

// 3. useCallback 优化回调
const handleDelete = useCallback((id) => deleteTicket(id), [])
```

**后端优化**：
- 检查慢查询（EXPLAIN ANALYZE）
- 使用 joinedload 避免 N+1 查询
- 验证索引使用

**验收标准**：
- ✅ 列表滚动流畅（60fps）
- ✅ API 响应 < 500ms
- ✅ 页面加载 < 2s

#### Day 4：错误处理和边界情况

**需要处理**：
- 空状态展示（空列表、空搜索结果）
- 错误提示（网络错误、API 错误）
- 加载状态（骨架屏已实现）

#### Day 5：质量检查

```bash
# 运行完整检查
cd env && ./check-running.sh

# 运行所有测试
docker exec project-alpha-backend bash -c \
  "source .venv/bin/activate && pytest -v"
```

---

### Week 2：精简部署上线

#### Day 1：准备部署环境

```bash
# 1. 服务器要求
- CPU: 2 核
- 内存: 4GB
- 硬盘: 40GB SSD
- 预估成本: ~100 元/月

# 2. 安装 Docker
curl -fsSL https://get.docker.com | sh
systemctl start docker && systemctl enable docker

# 3. 上传代码
rsync -avz --exclude node_modules --exclude .venv \
  Week1/ user@server:/app/project-alpha/
```

#### Day 2：执行部署

```bash
# 1. 启动服务
cd /app/project-alpha/env
docker compose up -d

# 2. 运行迁移
docker exec project-alpha-backend bash -c \
  "source .venv/bin/activate && alembic upgrade head"

# 3. 验证服务
curl http://localhost:8000/health
```

#### Day 3：HTTPS 和监控

```bash
# 使用 Caddy（最简单，自动 HTTPS）
apt install caddy

# Caddyfile 配置
your-domain.com {
    reverse_proxy /api/* localhost:8000
    reverse_proxy /* localhost:5173
}

# 设置数据库备份
crontab -e
# 0 2 * * * docker exec project-alpha-db pg_dump -U ticketuser ticketdb > /backup/db_$(date +\%Y\%m\%d).sql
```

---

### Week 3-4：观察期

- 邀请用户试用
- 收集使用反馈
- 记录功能需求
- 发现性能瓶颈
- 规划下一版本

---

## 📋 任务检查清单

### 本周必须完成（P0）✅

- [x] E2E 测试核心流程（Playwright 配置 + 3 个测试文件）
- [x] 性能基础优化（React.memo + useCallback）
- [x] 边界情况处理（空状态 + 错误提示优化）
- [x] 代码质量检查（Linter 无错误）

### 下周完成（P1）

- [ ] 准备部署环境
- [ ] 执行部署
- [ ] HTTPS 和监控配置

### 已完成的扩展功能 ✅

- [x] Toast 提示系统
- [x] 加载状态组件（骨架屏）
- [x] 错误边界（ErrorBoundary）
- [x] 分页组件
- [x] 键盘快捷键
- [x] 回收站页面（TrashPage）

### 后续根据反馈（P2 - 可选）

- [ ] 高级搜索（搜索历史、搜索高亮）
- [ ] 日期范围过滤
- [ ] 更多动画效果（列表动画、路由过渡）

---

## 💡 决策指南

### 场景 1：快速上线（1 周）

**执行**：P0（3 天）+ 精简部署（2 天）

**适合**：需要尽快获取用户反馈

### 场景 2：稳健上线（2 周）

**执行**：P0 + P1 全部（5 天）+ 完整部署（3 天）

**适合**：追求稳定性和完整性

### 场景 3：持续迭代（推荐）

**执行**：P0（3 天）→ 精简部署（2 天）→ 观察（2 周）→ 迭代

**适合**：敏捷开发，快速响应用户需求

---

## 🎉 总结

**一句话**：先稳定（测试）→ 再上线（部署）→ 后扩展（根据反馈）

**预计时间线**：
- 本周：完成测试与优化
- 下周：部署上线
- 第 3-4 周：观察收集反馈
- 之后：根据反馈迭代

**2 周后，系统正式上线！** 🚀

---

## 🔗 相关文档

- [PROJECT_STATUS.md](../PROJECT_STATUS.md) - 项目状态报告
- [0015-project-summary.md](./0015-project-summary.md) - 项目总结
- [0002-implementation-plan.md](./0002-implementation-plan.md) - 完整实施计划
